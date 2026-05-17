from __future__ import annotations 

import json 

import divination_fusion .adapters as adapters_module 
from divination_fusion .adapters import FakeAdapter ,ModelRequest ,OpenRouterAdapter ,validate_battler_payload 
from divination_fusion .models import Rebuttal 
from divination_fusion .session_store import SessionStore 

def test_fake_adapter_retries_until_valid_json ():
    adapter =FakeAdapter (
    responses =[
    "not-json",
    json .dumps (
    {
    "summary":"分析完成",
    "warnings":[],
    "claims":[
    {
    "dimension":"career",
    "statement":"事业维度有明显倾向。",
    "claim_type":"trend",
    "basis_type":"mock",
    "basis_value":"demo",
    "scope":"issue",
    "evidence":["证据 1"],
    "uncertainty_reasons":[],
    "required_inputs":[],
    "qualifiers":["fake"],
    "depends_on":[],
    "confidence":0.73 ,
    }
    ],
    },
    ensure_ascii =False ,
    ),
    ]
    )

    response =adapter .generate (
    ModelRequest (
    provider ="fake",
    model ="fake-model",
    role ="analyzer",
    system_name ="bazi",
    system_prompt ="system",
    user_prompt ="user",
    schema_name ="analyzer",
    )
    )

    assert response .attempts ==2 
    assert response .payload ["summary"]=="分析完成"
    assert response .payload ["claims"][0 ]["dimension"]=="career"

def test_session_store_persists_sessions_and_events (tmp_path ):
    store =SessionStore (root =tmp_path /"sessions",database_path =tmp_path /"sessions.sqlite3")

    record =store .create_session (
    session_id ="sess001",
    request_payload ={"query":"demo"},
    auth_mode ="server",
    )
    event =store .append_event (
    session_id ="sess001",
    event_type ="session_started",
    payload ={"query":"demo"},
    )
    updated =store .update_snapshot (
    session_id ="sess001",
    status ="completed",
    snapshot ={"status":"ok"},
    report ={"summary":"done"},
    )

    assert record .session_id =="sess001"
    assert event .seq ==1 
    assert updated .status =="completed"
    assert updated .snapshot =={"status":"ok"}
    assert updated .report =={"summary":"done"}
    assert (tmp_path /"sessions"/"sess001"/"request.json").is_file ()
    assert (tmp_path /"sessions"/"sess001"/"events.jsonl").is_file ()
    assert (tmp_path /"sessions"/"sess001"/"snapshot.json").is_file ()
    assert (tmp_path /"sessions"/"sess001"/"report.json").is_file ()

def test_validate_battler_payload_supports_dual_channel_fields ():
    payload =validate_battler_payload (
    {
    "stance":"maintain",
    "response":"内部回应",
    "public_response":"给前端展示的自然语言回应",
    "supported_claim_ids":[" claim-a ","claim-a","claim-b"],
    "conceded_points":[" 资料缺口  ","资料缺口"],
    "still_disputed_points":["核心分歧","核心分歧"],
    "argument_points":["强调长期趋势","强调长期趋势","补充边界条件"],
    "new_argument_points":["补充边界条件","  "],
    "summary_hint":" 本轮继续围绕长期趋势争论 ",
    "stop_signal":False ,
    "confidence":0.82 ,
    }
    )

    assert payload ["response"]=="内部回应"
    assert payload ["public_response"]=="给前端展示的自然语言回应"
    assert payload ["supported_claim_ids"]==["claim-a","claim-b"]
    assert payload ["conceded_points"]==["资料缺口"]
    assert payload ["still_disputed_points"]==["核心分歧"]
    assert payload ["argument_points"]==["强调长期趋势","补充边界条件"]
    assert payload ["new_argument_points"]==["补充边界条件"]
    assert payload ["summary_hint"]=="本轮继续围绕长期趋势争论"

def test_validate_battler_payload_backfills_public_fields ():
    payload =validate_battler_payload (
    {
    "stance":"maintain",
    "response":"只返回内部回应也能兼容。",
    "supported_claim_ids":["claim-a"],
    "conceded_points":[],
    "still_disputed_points":["仍有争议"],
    "stop_signal":True ,
    "confidence":0.68 ,
    }
    )

    assert payload ["public_response"]=="只返回内部回应也能兼容。"
    assert payload ["argument_points"]==[]
    assert payload ["new_argument_points"]==[]
    assert payload ["summary_hint"]=="只返回内部回应也能兼容。"

def test_fake_adapter_battler_returns_dual_channel_payload ():
    adapter =FakeAdapter ()

    response =adapter .generate (
    ModelRequest (
    provider ="fake",
    model ="fake-model",
    role ="battler",
    system_name ="bazi",
    system_prompt ="system",
    user_prompt ="user",
    schema_name ="battler",
    )
    )

    assert response .payload ["response"]=="bazi 保持原判断。"
    assert response .payload ["public_response"]=="bazi 的公开回应：保持原判断。"
    assert response .payload ["argument_points"]==["维持原判断"]
    assert response .payload ["new_argument_points"]==[]
    assert response .payload ["summary_hint"]=="bazi 继续坚持原判断。"

def test_rebuttal_defaults_public_response_and_summary_hint ():
    rebuttal =Rebuttal (
    issue_id ="issue-1",
    round_index =1 ,
    system ="bazi",
    response ="内部响应",
    supported_claim_ids =["claim-a"],
    )

    assert rebuttal .public_response =="内部响应"
    assert rebuttal .summary_hint =="内部响应"

def test_openrouter_adapter_uses_openrouter_endpoint_and_headers (monkeypatch ):
    captured :dict [str ,object ]={}

    def fake_post_json (url ,payload ,*,headers ):
        captured ["url"]=url 
        captured ["payload"]=payload 
        captured ["headers"]=headers 
        return {
        "choices":[
        {
        "message":{
        "content":'{"summary":"ok","warnings":[],"claims":[{"dimension":"career","statement":"稳定。","claim_type":"trend","basis_type":"mock","basis_value":"demo","scope":"issue","evidence":["证据"],"uncertainty_reasons":[],"required_inputs":[],"qualifiers":[],"depends_on":[],"confidence":0.8}]}'
        }
        }
        ]
        }

    monkeypatch .setattr (adapters_module ,"_post_json",fake_post_json )
    adapter =OpenRouterAdapter ()

    response =adapter .generate (
    ModelRequest (
    provider ="openrouter",
    model ="openrouter/auto",
    role ="analyzer",
    system_name ="bazi",
    system_prompt ="system",
    user_prompt ="user",
    schema_name ="analyzer",
    api_key ="test-key",
    )
    )

    assert captured ["url"]=="https://openrouter.ai/api/v1/chat/completions"
    headers =captured ["headers"]
    payload =captured ["payload"]
    assert headers ["Authorization"]=="Bearer test-key"
    assert headers ["HTTP-Referer"]=="https://conclave-ai.local"
    assert headers ["X-OpenRouter-Title"]=="divination-fusion"
    assert payload ["max_tokens"]==4096 
    assert response .payload ["summary"]=="ok"
