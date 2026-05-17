from __future__ import annotations 

from pathlib import Path 
from typing import Optional ,Union 

from divination_fusion .workflow import run_analysis ,state_to_dict 

from .dataset import EvalCase ,build_demo_dataset 

def evaluate_case (case :EvalCase ,*,trace_root :Union [str ,Path ]="runs/evals")->dict [str ,object ]:
    state =run_analysis (case .request ,trace_root =trace_root )
    report =state .fusion_report 
    issue_relations ={issue .dimension :issue .relation .value for issue in state .debate_issues }
    missing_fields =state .normalized_profile .missing_fields if state .normalized_profile else []
    followups =report .suggested_followups if report else []
    reservations =report .reservations if report else []
    checks =_evaluate_expectations (
    case ,
    missing_fields =missing_fields ,
    issue_relations =issue_relations ,
    followups =followups ,
    reservations =reservations ,
    report =report ,
    )
    return {
    "case_id":case .case_id ,
    "passed":all (check ["passed"]for check in checks ),
    "focus_areas":case .request .focus_areas ,
    "expected_focus_areas":case .expected_focus_areas ,
    "summary":report .summary if report else "",
    "missing_fields":missing_fields ,
    "issue_relations":issue_relations ,
    "checks":checks ,
    "state":state_to_dict (state ),
    }

def evaluate_dataset (
cases :Optional [list [EvalCase ]]=None ,
*,
trace_root :Union [str ,Path ]="runs/evals",
)->list [dict [str ,object ]]:
    selected_cases =cases or build_demo_dataset ()
    return [evaluate_case (case ,trace_root =trace_root )for case in selected_cases ]

def run_demo_eval (*,trace_root :Union [str ,Path ]="runs/evals")->list [dict [str ,object ]]:
    return evaluate_dataset (trace_root =trace_root )

def _evaluate_expectations (
case :EvalCase ,
*,
missing_fields :list [str ],
issue_relations :dict [str ,str ],
followups :list [str ],
reservations :list [str ],
report :object ,
)->list [dict [str ,object ]]:
    checks :list [dict [str ,object ]]=[]
    checks .append (
    {
    "name":"summary_present",
    "passed":bool (report and getattr (report ,"summary","")),
    "details":"summary should be non-empty",
    }
    )
    checks .append (
    {
    "name":"focus_areas_match",
    "passed":sorted (case .request .focus_areas )==sorted (case .expected_focus_areas ),
    "details":{
    "actual":case .request .focus_areas ,
    "expected":case .expected_focus_areas ,
    },
    }
    )
    checks .append (
    {
    "name":"raw_sections_complete",
    "passed":bool (report and _raw_sections_complete (report .raw_sections )),
    "details":"report should keep the expected section layout",
    }
    )

    for field_name in case .required_missing_fields :
        checks .append (
        {
        "name":f"missing_field:{field_name}",
        "passed":field_name in missing_fields ,
        "details":{
        "actual":missing_fields ,
        "expected_contains":field_name ,
        },
        }
        )

    for dimension ,relation in case .required_issue_relations .items ():
        checks .append (
        {
        "name":f"issue_relation:{dimension}",
        "passed":issue_relations .get (dimension )==relation ,
        "details":{
        "actual":issue_relations .get (dimension ),
        "expected":relation ,
        },
        }
        )

    for keyword in case .required_followup_keywords :
        checks .append (
        {
        "name":f"followup:{keyword}",
        "passed":_contains_keyword (followups ,keyword ),
        "details":{
        "expected_keyword":keyword ,
        "actual":followups ,
        },
        }
        )

    for keyword in case .required_reservation_keywords :
        checks .append (
        {
        "name":f"reservation:{keyword}",
        "passed":_contains_keyword (reservations ,keyword ),
        "details":{
        "expected_keyword":keyword ,
        "actual":reservations ,
        },
        }
        )

    return checks 

def _raw_sections_complete (raw_sections :dict [str ,object ])->bool :
    expected_order =["结论摘要","共识","分歧","保留意见","建议补充资料","可继续追问点"]
    return list (raw_sections .keys ())==expected_order 

def _contains_keyword (items :list [str ],keyword :str )->bool :
    return any (keyword in item for item in items )
