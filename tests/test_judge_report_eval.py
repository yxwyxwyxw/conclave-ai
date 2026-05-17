from divination_fusion .agents import build_analysis_request 
from divination_fusion .battle import (
build_cross_exam_questions ,
build_rebuttals ,
detect_debate_issues ,
map_dimensions ,
run_battle ,
)
from divination_fusion .evals import build_demo_dataset ,evaluate_case ,evaluate_dataset 
from divination_fusion .judge import apply_judgement_reviews ,judge_issues ,review_judgements 
from divination_fusion .models import (
Claim ,
ClaimRelation ,
DebateIssue ,
Judgement ,
JudgementDisposition ,
SystemEvidence ,
)
from divination_fusion .report import synthesize_report 
from divination_fusion .services import normalize_profile 
from divination_fusion .systems .astrology import analyze_astrology 
from divination_fusion .systems .bazi import analyze_bazi 
from divination_fusion .workflow import run_analysis 

def test_judge_and_report_and_eval_smoke (tmp_path ):
    request =build_analysis_request (
    "请综合分析我的事业和感情趋势",
    name ="Smoke Test",
    birth_date ="1990-06-12",
    birth_time ="07:45",
    birth_place ="Shanghai",
    timezone ="Asia/Shanghai",
    )
    profile =normalize_profile (request )
    evidence_list =[analyze_bazi (request ,profile ),analyze_astrology (request ,profile )]
    mapped =map_dimensions (evidence_list )
    issues =detect_debate_issues (evidence_list ,mapped )
    cross_exam =build_cross_exam_questions (issues ,evidence_list )
    rebuttals =build_rebuttals (cross_exam ,issues ,evidence_list )

    judgements =judge_issues (issues ,evidence_list ,rebuttals )
    assert isinstance (judgements ,list )
    assert all (judgement .cited_claim_ids for judgement in judgements )

    report =synthesize_report (request ,profile ,evidence_list ,judgements ,issues )
    assert report .summary 
    assert report .raw_sections ["结论摘要"]==report .summary 
    assert list (report .raw_sections .keys ())==["结论摘要","共识","分歧","保留意见","建议补充资料","可继续追问点"]
    conditional_judgements =[judgement for judgement in judgements if judgement .disposition .value =="conditional"]
    if conditional_judgements :
        assert "条件"in report .summary 
        assert any ("条件"in item for item in report .reservations )
        assert any ("条件"in item for item in report .suggested_followups )
        for judgement in conditional_judgements :
            assert all (judgement .rationale not in item for item in report .consensus_points )

    workflow_state =run_analysis (request ,trace_root =tmp_path )
    assert workflow_state .fusion_report is not None 
    assert workflow_state .judgements 
    assert workflow_state .judgement_reviews 

    demo_cases =build_demo_dataset ()
    result =evaluate_case (demo_cases [0 ],trace_root =tmp_path )
    assert result ["case_id"]==demo_cases [0 ].case_id 
    assert any (check ["name"]=="summary_present"and check ["passed"]for check in result ["checks"])
    assert any (check ["name"]=="raw_sections_complete"and check ["passed"]for check in result ["checks"])

def test_demo_dataset_covers_baseline_eval_paths (tmp_path ):
    results =evaluate_dataset (trace_root =tmp_path )

    assert len (results )==3 
    assert {result ["case_id"]for result in results }=={
    "full-info-career-relationship",
    "date-only-health",
    "career-tension-focus",
    }
    assert all (any (check ["name"]=="summary_present"and check ["passed"]for check in result ["checks"])for result in results )
    assert all (any (check ["name"]=="raw_sections_complete"and check ["passed"]for check in result ["checks"])for result in results )

    date_only =next (result for result in results if result ["case_id"]=="date-only-health")
    assert "birth_time"in date_only ["missing_fields"]
    assert any (check ["name"]=="followup:优先补充出生时辰"and check ["passed"]for check in date_only ["checks"])

    career_focus =next (result for result in results if result ["case_id"]=="career-tension-focus")
    assert career_focus ["expected_focus_areas"]==["career"]

def test_judge_marks_referee_termination_after_round_cap ():
    request =build_analysis_request (
    "请综合分析我的事业、感情和性格优势",
    name ="Round Cap",
    birth_date ="1990-06-12",
    birth_time ="07:45",
    birth_place ="Shanghai",
    timezone ="Asia/Shanghai",
    )
    profile =normalize_profile (request )
    evidence_list =[analyze_bazi (request ,profile ),analyze_astrology (request ,profile )]
    issues =detect_debate_issues (evidence_list ,map_dimensions (evidence_list ))
    _questions ,rebuttals =run_battle (issues ,evidence_list ,max_rounds =4 )

    judgements =judge_issues (issues ,evidence_list ,rebuttals )

    assert any ("由裁判终局"in " ".join (judgement .conditions )for judgement in judgements )

def test_review_judgements_flags_invalid_claim_references_and_missing_reservations ():
    evidence_list =[
    SystemEvidence (
    system ="bazi",
    summary ="summary",
    data_quality =0.8 ,
    claims =[
    Claim (
    claim_id ="bazi-career-1",
    system ="bazi",
    dimension ="career",
    statement ="事业上升",
    evidence =["四柱结构支持"],
    )
    ],
    ),
    SystemEvidence (
    system ="astrology",
    summary ="summary",
    data_quality =0.8 ,
    claims =[
    Claim (
    claim_id ="astro-career-1",
    system ="astrology",
    dimension ="career",
    statement ="事业有波动",
    evidence =["土星相位带来压力"],
    )
    ],
    ),
    ]
    issues =[
    DebateIssue (
    issue_id ="career-1",
    dimension ="career",
    relation =ClaimRelation .CONTRADICTION ,
    claim_ids =["bazi-career-1","astro-career-1"],
    question ="事业走势是否稳定",
    severity =0.8 ,
    rounds_completed =6 ,
    termination_reason ="max-rounds-reached",
    )
    ]
    judgements =[
    Judgement (
    issue_id ="career-1",
    disposition =JudgementDisposition .FAVOR_A ,
    favored_system ="bazi",
    rationale ="原始裁决。",
    conditions =[],
    cited_claim_ids =["bazi-career-1","ghost-claim"],
    )
    ]

    reviews =review_judgements (judgements ,issues ,evidence_list )

    assert len (reviews )==1 
    review =reviews [0 ]
    assert not review .passed 
    assert review .invalid_cited_claim_ids ==["ghost-claim"]
    assert any ("由裁判终局"in item for item in review .extra_conditions )
    assert any ("不存在的 claim"in item for item in review .extra_conditions )

def test_apply_judgement_reviews_merges_verifier_feedback ():
    evidence_list =[
    SystemEvidence (
    system ="bazi",
    summary ="summary",
    data_quality =0.8 ,
    claims =[
    Claim (
    claim_id ="bazi-risk-1",
    system ="bazi",
    dimension ="risk",
    statement ="资料不足",
    evidence =["缺少出生时辰"],
    )
    ],
    )
    ]
    issues =[
    DebateIssue (
    issue_id ="risk-1",
    dimension ="risk",
    relation =ClaimRelation .INSUFFICIENT_DATA ,
    claim_ids =["bazi-risk-1"],
    question ="风险判断是否足够稳定",
    severity =0.6 ,
    termination_reason ="single-sided-issue",
    )
    ]
    judgements =[
    Judgement (
    issue_id ="risk-1",
    disposition =JudgementDisposition .UNRESOLVED ,
    favored_system =None ,
    rationale ="当前保守保留。",
    conditions =[],
    cited_claim_ids =["bazi-risk-1"],
    )
    ]

    reviews =review_judgements (judgements ,issues ,evidence_list )
    merged =apply_judgement_reviews (judgements ,reviews )

    assert len (merged )==1 
    merged_judgement =merged [0 ]
    assert any ("资料不足"in item for item in merged_judgement .conditions )
    assert any ("单侧体系"in item for item in merged_judgement .conditions )
    assert "复核"in merged_judgement .rationale 
