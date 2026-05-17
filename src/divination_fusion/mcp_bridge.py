from __future__ import annotations 

import json 
import subprocess 
import threading 
from typing import Any 

_MCP_INITIALIZE =json .dumps (
{
"jsonrpc":"2.0",
"id":0 ,
"method":"initialize",
"params":{
"protocolVersion":"2024-11-05",
"capabilities":{},
"clientInfo":{"name":"divination-fusion","version":"0.1.0"},
},
}
)
_MCP_INITIALIZED =json .dumps (
{"jsonrpc":"2.0","method":"notifications/initialized"}
)

class MCPError (RuntimeError ):
    pass 

class MCPClient :
    """Lightweight MCP JSON-RPC client that talks to a Node.js MCP server over stdio."""

    def __init__ (self ,command :list [str ])->None :
        self ._command =command 
        self ._proc :subprocess .Popen [str ]|None =None 
        self ._lock =threading .Lock ()
        self ._next_id =1 

    def _ensure_started (self )->subprocess .Popen [str ]:
        if self ._proc is not None and self ._proc .poll ()is None :
            return self ._proc 
        self ._proc =subprocess .Popen (
        self ._command ,
        stdin =subprocess .PIPE ,
        stdout =subprocess .PIPE ,
        stderr =subprocess .PIPE ,
        text =True ,
        bufsize =1 ,
        )
        self ._send (_MCP_INITIALIZE )
        self ._read_response (id_ =0 )
        self ._send (_MCP_INITIALIZED )
        return self ._proc 

    def call_tool (self ,tool_name :str ,arguments :dict [str ,Any ])->dict [str ,Any ]:
        with self ._lock :
            proc =self ._ensure_started ()
            request_id =self ._next_id 
            self ._next_id +=1 
            payload =json .dumps (
            {
            "jsonrpc":"2.0",
            "id":request_id ,
            "method":"tools/call",
            "params":{"name":tool_name ,"arguments":arguments },
            },
            ensure_ascii =False ,
            )
            self ._send (payload )
            response =self ._read_response (id_ =request_id )
        if "error"in response :
            raise MCPError (response ["error"].get ("message",str (response ["error"])))
        result =response .get ("result",{})
        content =result .get ("content",[])
        if not content :
            raise MCPError ("MCP 返回了空 content")
        text =content [0 ].get ("text","")
        if not text :
            raise MCPError ("MCP 返回的 text 为空")
        try :
            return json .loads (text )
        except json .JSONDecodeError :
            return {"text":text }

    def _send (self ,message :str )->None :
        assert self ._proc and self ._proc .stdin 
        self ._proc .stdin .write (message +"\n")
        self ._proc .stdin .flush ()

    def _read_response (self ,*,id_ :int )->dict [str ,Any ]:
        assert self ._proc and self ._proc .stdout 
        while True :
            line =self ._proc .stdout .readline ()
            if not line :
                stderr_text =""
                if self ._proc .stderr :
                    stderr_text =self ._proc .stderr .read ()
                raise MCPError (f"MCP 进程意外退出。stderr: {stderr_text[:500]}")
            try :
                data =json .loads (line )
            except json .JSONDecodeError :
                continue 
            if data .get ("id")==id_ :
                return data 

    def close (self )->None :
        if self ._proc :
            try :
                self ._proc .terminate ()
                self ._proc .wait (timeout =5 )
            except Exception :
                self ._proc .kill ()
            self ._proc =None 

_bazi_client :MCPClient |None =None 
_ziwei_client :MCPClient |None =None 
_lock =threading .Lock ()

def _get_bazi_client ()->MCPClient :
    global _bazi_client 
    if _bazi_client is None :
        _bazi_client =MCPClient (["npx","-y","shunshi-bazi-mcp"])
    return _bazi_client 

def _get_ziwei_client ()->MCPClient :
    global _ziwei_client 
    if _ziwei_client is None :
        _ziwei_client =MCPClient (["npx","-y","ziwei-mcp"])
    return _ziwei_client 

def get_bazi_chart (
year :int ,
month :int ,
day :int ,
hour :int ,
minute :int =0 ,
gender :str ="male",
city :str |None =None ,
longitude :float |None =None ,
latitude :float |None =None ,
use_true_solar_time :bool =True ,
)->dict [str ,Any ]:
    """Call shunshi-bazi-mcp getBaziChart and return the parsed chart dict."""
    gender_code =1 if gender in ("male","男")else 0 
    args :dict [str ,Any ]={
    "year":year ,
    "month":month ,
    "day":day ,
    "hour":hour ,
    "minute":minute ,
    "gender":gender_code ,
    "useTrueSolarTime":use_true_solar_time ,
    "sect":1 ,
    }
    if city :
        args ["city"]=city 
    if longitude is not None and latitude is not None :
        args ["longitude"]=longitude 
        args ["latitude"]=latitude 

    client =_get_bazi_client ()
    return client .call_tool ("getBaziChart",args )

def generate_ziwei_chart (
name :str |None =None ,
gender :str ="male",
birth_date :str ="",
birth_time :str ="",
birth_location :str |None =None ,
)->dict [str ,Any ]:
    """Call ziwei-mcp generate_chart and return the parsed chart dict."""
    args :dict [str ,Any ]={
    "gender":gender ,
    "birthDate":birth_date ,
    "birthTime":birth_time ,
    }
    if name :
        args ["name"]=name 
    if birth_location :
        args ["birthLocation"]=birth_location 

    client =_get_ziwei_client ()
    return client .call_tool ("generate_chart",args )
