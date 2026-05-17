from __future__ import annotations 

from contextlib import suppress 
import json 
import os 
from pathlib import Path 
import queue 
import threading 
from typing import Any ,Optional 
from uuid import uuid4 

from fastapi import Depends ,FastAPI ,HTTPException ,Request ,Response 
from fastapi .responses import HTMLResponse ,JSONResponse ,StreamingResponse 
from pydantic import BaseModel ,Field 
import uvicorn 

from divination_fusion .adapters import AdapterRegistry 
from divination_fusion .auth import COOKIE_NAME ,admin_password ,require_admin ,sign_session 
from divination_fusion .orchestrator import BattleOrchestrator ,SessionRunInput 
from divination_fusion .session_store import SessionStore 
from divination_fusion .web_ui import APP_HTML 

class RoleConfigPayload (BaseModel ):
    provider :str 
    model :str 

class SessionCreatePayload (BaseModel ):
    query :str 
    name :Optional [str ]=None 
    birth_date :Optional [str ]=None 
    birth_time :Optional [str ]=None 
    birth_place :Optional [str ]=None 
    timezone :Optional [str ]=None 
    max_battle_rounds :int =Field (default =6 ,ge =1 ,le =50 )
    credential_mode :str =Field (default ="server")
    provider_configs :dict [str ,RoleConfigPayload ]
    openai_api_key :Optional [str ]=None 
    deepseek_api_key :Optional [str ]=None 
    openrouter_api_key :Optional [str ]=None 
    anthropic_api_key :Optional [str ]=None 

class LoginPayload (BaseModel ):
    password :str 

def create_app (
*,
store :SessionStore |None =None ,
adapters :AdapterRegistry |None =None ,
)->FastAPI :
    app =FastAPI (title ="Divination Fusion Web")
    app .state .store =store or SessionStore ()
    app .state .adapters =adapters or AdapterRegistry ()
    app .state .orchestrator =BattleOrchestrator (app .state .store ,app .state .adapters )
    app .state .cancel_events :dict [str ,threading .Event ]={}
    app .state .threads :dict [str ,threading .Thread ]={}

    @app .get ("/",response_class =HTMLResponse )
    def index ()->str :
        return APP_HTML 

    @app .post ("/api/login")
    def login (payload :LoginPayload ,response :Response )->dict [str ,str ]:
        if payload .password !=admin_password ():
            raise HTTPException (status_code =401 ,detail ="invalid_password")
        response .set_cookie (
        COOKIE_NAME ,
        sign_session ("admin"),
        httponly =True ,
        samesite ="lax",
        max_age =60 *60 *8 ,
        )
        return {"status":"ok"}

    @app .post ("/api/logout")
    def logout (response :Response )->dict [str ,str ]:
        response .delete_cookie (COOKIE_NAME )
        return {"status":"ok"}

    @app .get ("/api/sessions")
    def list_sessions (_admin :str =Depends (require_admin ))->list [dict [str ,Any ]]:
        return [_public_session_view (record )for record in app .state .store .list_sessions ()]

    @app .get ("/api/sessions/{session_id}")
    def get_session (session_id :str ,_admin :str =Depends (require_admin ))->dict [str ,Any ]:
        try :
            record =app .state .store .get_session (session_id )
        except KeyError as exc :
            raise HTTPException (status_code =404 ,detail ="session_not_found")from exc 
        payload =_public_session_view (record )
        payload ["events"]=[event .payload |{"event_type":event .event_type ,"seq":event .seq }for event in app .state .store .list_events (session_id )]
        return payload 

    @app .post ("/api/sessions")
    def create_session (payload :SessionCreatePayload ,_admin :str =Depends (require_admin ))->dict [str ,str ]:
        required_roles ={
        "bazi_analyzer",
        "ziwei_analyzer",
        "bazi_battler",
        "ziwei_battler",
        "judge",
        }
        missing_roles =sorted (required_roles -set (payload .provider_configs ))
        if missing_roles :
            raise HTTPException (status_code =422 ,detail =f"缺少角色配置: {', '.join(missing_roles)}")
        session_id =uuid4 ().hex [:12 ]
        sanitized_payload =payload .model_dump ()
        sanitized_payload ["openai_api_key"]=None 
        sanitized_payload ["deepseek_api_key"]=None 
        sanitized_payload ["openrouter_api_key"]=None 
        sanitized_payload ["anthropic_api_key"]=None 
        app .state .store .create_session (
        session_id =session_id ,
        request_payload =sanitized_payload ,
        auth_mode =payload .credential_mode ,
        )
        api_keys =_resolve_api_keys (payload )
        run_input =SessionRunInput (
        query =payload .query ,
        name =payload .name ,
        birth_date =payload .birth_date ,
        birth_time =payload .birth_time ,
        birth_place =payload .birth_place ,
        timezone =payload .timezone ,
        max_battle_rounds =payload .max_battle_rounds ,
        credential_mode =payload .credential_mode ,
        provider_configs ={key :value .model_dump ()for key ,value in payload .provider_configs .items ()},
        api_keys =api_keys ,
        )
        cancel_event =threading .Event ()
        app .state .cancel_events [session_id ]=cancel_event 
        thread =threading .Thread (
        target =_run_session_thread ,
        args =(app .state .orchestrator ,session_id ,run_input ,cancel_event ),
        daemon =True ,
        )
        app .state .threads [session_id ]=thread 
        thread .start ()
        return {"session_id":session_id }

    @app .post ("/api/sessions/{session_id}/cancel")
    def cancel_session (session_id :str ,_admin :str =Depends (require_admin ))->dict [str ,str ]:
        event =app .state .cancel_events .get (session_id )
        if event is None :
            raise HTTPException (status_code =404 ,detail ="session_not_found")
        event .set ()
        return {"status":"cancel_requested"}

    @app .get ("/api/sessions/{session_id}/events")
    def stream_events (session_id :str ,request :Request ,_admin :str =Depends (require_admin ))->StreamingResponse :
        try :
            record =app .state .store .get_session (session_id )
        except KeyError as exc :
            raise HTTPException (status_code =404 ,detail ="session_not_found")from exc 

        subscriber =app .state .store .subscribe (session_id )
        past_events =app .state .store .list_events (session_id )

        def event_stream ():
            try :
                for event in past_events :
                    yield _encode_sse (event )
                while True :
                    try :
                        event =subscriber .get (timeout =1 )
                        yield _encode_sse (event )
                    except queue .Empty :
                        current =app .state .store .get_session (session_id )
                        if current .status in {"completed","failed","cancelled"}:
                            break 
                        continue 
            finally :
                app .state .store .unsubscribe (session_id ,subscriber )

        headers ={
        "Cache-Control":"no-cache",
        "X-Accel-Buffering":"no",
        }
        return StreamingResponse (event_stream (),media_type ="text/event-stream",headers =headers )

    return app 

def _run_session_thread (
orchestrator :BattleOrchestrator ,
session_id :str ,
run_input :SessionRunInput ,
cancel_event :threading .Event ,
)->None :
    try :
        orchestrator .run (session_id ,run_input ,cancel_event =cancel_event )
    except Exception as exc :
        with suppress (Exception ):
            record =orchestrator .store .get_session (session_id )
            if record .status =="running":
                orchestrator .store .update_snapshot (
                session_id =session_id ,
                status ="failed",
                snapshot =record .snapshot ,
                )
                orchestrator .store .append_event (
                session_id =session_id ,
                event_type ="session_failed",
                payload ={"error":str (exc )},
                )

def _encode_sse (event :Any )->str :
    payload ={
    "seq":event .seq ,
    "session_id":event .session_id ,
    "event_type":event .event_type ,
    "created_at":event .created_at ,
    "issue_id":event .issue_id ,
    "round_index":event .round_index ,
    **event .payload ,
    }
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

def _public_session_view (record :Any )->dict [str ,Any ]:
    return {
    "session_id":record .session_id ,
    "status":record .status ,
    "created_at":record .created_at ,
    "updated_at":record .updated_at ,
    "auth_mode":record .auth_mode ,
    "request_payload":record .request_payload ,
    "snapshot":record .snapshot ,
    "report":record .report ,
    "run_dir":record .run_dir ,
    }

def _resolve_api_keys (payload :SessionCreatePayload )->dict [str ,str ]:
    local_env =_load_project_env ()
    if payload .credential_mode =="byok":
        keys ={
        "openai":payload .openai_api_key or "",
        "deepseek":payload .deepseek_api_key or "",
        "openrouter":payload .openrouter_api_key or "",
        "anthropic":payload .anthropic_api_key or "",
        }
    else :
        keys ={
        "openai":os .getenv ("OPENAI_API_KEY","")or local_env .get ("OPENAI_API_KEY",""),
        "deepseek":os .getenv ("DEEPSEEK_API_KEY","")or local_env .get ("DEEPSEEK_API_KEY",""),
        "openrouter":os .getenv ("OPENROUTER_API_KEY","")or local_env .get ("OPENROUTER_API_KEY",""),
        "anthropic":os .getenv ("ANTHROPIC_API_KEY","")or local_env .get ("ANTHROPIC_API_KEY",""),
        }
    resolved ={provider :key for provider ,key in keys .items ()if key }
    configured_providers ={config .provider for config in payload .provider_configs .values ()if config .provider !="fake"}
    missing =sorted (provider for provider in configured_providers if provider not in resolved )
    if missing :
        raise HTTPException (status_code =422 ,detail =f"缺少 provider key: {', '.join(missing)}")
    return resolved 

def _load_project_env ()->dict [str ,str ]:
    root =Path .cwd ()
    env_path =root /".env"
    if not env_path .is_file ():
        return {}
    result :dict [str ,str ]={}
    for raw_line in env_path .read_text (encoding ="utf-8").splitlines ():
        line =raw_line .strip ()
        if not line or line .startswith ("#")or "="not in line :
            continue 
        key ,value =line .split ("=",1 )
        result [key .strip ()]=value .strip ().strip ('"').strip ("'")
    return result 

app =create_app ()

def main ()->None :
    uvicorn .run (
    "divination_fusion.webapp:app",
    host ="127.0.0.1",
    port =8000 ,
    reload =False ,
    )

if __name__ =="__main__":
    main ()
