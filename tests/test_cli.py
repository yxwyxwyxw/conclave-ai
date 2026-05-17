from __future__ import annotations 

from pathlib import Path 

import pytest 

from divination_fusion .cli import build_parser ,build_request_from_args ,replay_output_from_args 
from divination_fusion .workflow import run_analysis 
from divination_fusion .agents import build_analysis_request 

def test_parser_requires_demo_or_query ()->None :
    parser =build_parser ()

    with pytest .raises (SystemExit ):
        parser .parse_args ([])

def test_demo_mode_rejects_extra_inputs ()->None :
    parser =build_parser ()
    args =parser .parse_args (["--demo","--birth-date","1990-01-01"])

    with pytest .raises (ValueError ,match ="demo 只能单独使用"):
        build_request_from_args (args )

def test_query_mode_uses_provided_fields ()->None :
    parser =build_parser ()
    args =parser .parse_args (
    [
    "--query",
    "我想看事业和感情",
    "--name",
    "  Demo User  ",
    "--birth-date",
    "1990-06-12",
    "--birth-time",
    "07:45",
    "--birth-place",
    "Shanghai",
    "--timezone",
    "Asia/Shanghai",
    "--max-battle-rounds",
    "9",
    "--trace-root",
    "runs/test",
    ]
    )

    request =build_request_from_args (args )

    assert request .query =="我想看事业和感情"
    assert request .profile .name =="  Demo User  "
    assert request .profile .birth_date =="1990-06-12"
    assert request .profile .birth_time =="07:45"
    assert request .profile .birth_place =="Shanghai"
    assert request .profile .timezone =="Asia/Shanghai"
    assert request .metadata ["max_battle_rounds"]==9 
    assert args .trace_root ==Path ("runs/test")

def test_demo_mode_builds_bundled_request ()->None :
    parser =build_parser ()
    args =parser .parse_args (["--demo"])

    request =build_request_from_args (args )

    assert request .query =="请综合分析我的事业、感情和性格优势"
    assert request .profile .name =="Demo User"

def test_replay_trace_mode_rejects_extra_inputs ()->None :
    parser =build_parser ()
    args =parser .parse_args (["--replay-trace","runs/demo","--max-battle-rounds","8"])

    with pytest .raises (ValueError ,match ="replay-trace 只能单独使用"):
        replay_output_from_args (args )

def test_replay_trace_mode_returns_structured_summary (tmp_path :Path )->None :
    request =build_analysis_request (
    "请综合分析我的事业和感情趋势",
    name ="CLI Replay",
    birth_date ="1990-06-12",
    birth_time ="07:45",
    birth_place ="Shanghai",
    timezone ="Asia/Shanghai",
    )
    state =run_analysis (request ,trace_root =tmp_path )
    parser =build_parser ()
    trace_dir =tmp_path /state .trace_metadata .run_id 
    args =parser .parse_args (["--replay-trace",str (trace_dir )])

    replay =replay_output_from_args (args )

    assert replay ["run_id"]==state .trace_metadata .run_id 
    assert replay ["step_count"]==5 
