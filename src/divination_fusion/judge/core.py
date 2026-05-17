from __future__ import annotations 

from collections import defaultdict 
from dataclasses import dataclass ,field 
from typing import List ,Optional ,Tuple 

from divination_fusion .models import (
Claim ,
ClaimRelation ,
DebateIssue ,
Judgement ,
JudgementDisposition ,
Rebuttal ,
SystemEvidence ,
)

_SYSTEM_LABELS ={
"bazi":"八字",
"astrology":"星盘",
"ziwei":"紫微",
}

_DIMENSION_LABELS ={
"career":"事业",
"personality":"性格",
"relationship":"感情",
"risk":"风险",
"health":"健康",
"wealth":"财务",
}

@dataclass 
class JudgementReview :
    issue_id :str 
    passed :bool 
    extra_conditions :list [str ]=field (default_factory =list )
    rationale_appendix :Optional [str ]=None 
    invalid_cited_claim_ids :list [str ]=field (default_factory =list )
    missing_reservations :list [str ]=field (default_factory =list )

def judge_issues (
issues :list [DebateIssue ],
evidence_list :list [SystemEvidence ],
rebuttals :list [Rebuttal ],
)->list [Judgement ]:
    claim_index =_claim_index (evidence_list )
    rebuttal_index =_rebuttal_index (rebuttals )
    judgements :list [Judgement ]=[]

    for issue in issues :
        claims =[claim_index [cid ]for cid in issue .claim_ids if cid in claim_index ]
        if not claims :
            issue_rebuttals =rebuttal_index .get (issue .issue_id ,[])
            disposition =JudgementDisposition .CONDITIONAL if issue_rebuttals else JudgementDisposition .UNRESOLVED 
            judgements .append (
            Judgement (
            issue_id =issue .issue_id ,
            disposition =disposition ,
            favored_system =issue_rebuttals [-1 ].system if issue_rebuttals else None ,
            rationale ="当前没有稳定的结构化证据索引，只能根据已有文本先做保守判断。",
            conditions =["补充更多结构化证据后再裁决"],
            cited_claim_ids =[],
            summary ="当前只能保守保留。",
            )
            )
            continue 

        system_scores =_system_scores (claims )
        top_system ,top_score =max (system_scores .items (),key =lambda item :item [1 ])
        sorted_scores =sorted (system_scores .items (),key =lambda item :item [1 ],reverse =True )
        second_score =sorted_scores [1 ][1 ]if len (sorted_scores )>1 else 0.0 
        issue_rebuttals =rebuttal_index .get (issue .issue_id ,[])

        disposition ,favored_system ,conditions =_decide (
        issue ,
        top_system ,
        top_score ,
        second_score ,
        claims ,
        )
        conditions =_merge_conditions (conditions ,_battle_conditions (issue ))
        rationale =_build_rationale (
        issue ,
        claims ,
        issue_rebuttals ,
        disposition ,
        favored_system ,
        conditions ,
        )
        cited_claim_ids =[claim .claim_id for claim in claims ]
        for rebuttal in issue_rebuttals :
            cited_claim_ids .extend (rebuttal .supported_claim_ids )

        judgements .append (
        Judgement (
        issue_id =issue .issue_id ,
        disposition =disposition ,
        favored_system =favored_system ,
        rationale =rationale ,
        conditions =conditions ,
        cited_claim_ids =_dedupe (cited_claim_ids ),
        summary =_summarize_judgement (issue ,disposition ,favored_system ),
        )
        )

    return judgements 

def review_judgements (
judgements :list [Judgement ],
issues :list [DebateIssue ],
evidence_list :list [SystemEvidence ],
)->list [JudgementReview ]:
    claim_index =_claim_index (evidence_list )
    issue_index ={issue .issue_id :issue for issue in issues }
    reviews :list [JudgementReview ]=[]

    for judgement in judgements :
        issue =issue_index .get (judgement .issue_id )
        invalid_cited_claim_ids =[
        claim_id for claim_id in judgement .cited_claim_ids if claim_id not in claim_index 
        ]
        extra_conditions :list [str ]=[]
        missing_reservations :list [str ]=[]

        if invalid_cited_claim_ids :
            extra_conditions .append (
            "复核发现裁决引用了不存在的 claim："
            +"、".join (invalid_cited_claim_ids )
            +"；这些引用不应继续作为裁判依据"
            )

        if issue is not None :
            required_conditions =_required_reservations (issue )
            missing_reservations =[
            item for item in required_conditions if not _has_matching_condition (judgement .conditions ,item )
            ]
            extra_conditions .extend (missing_reservations )

        rationale_appendix =None 
        if invalid_cited_claim_ids or missing_reservations :
            parts :list [str ]=[]
            if invalid_cited_claim_ids :
                parts .append ("已标记无效引用并建议从最终依据中剔除")
            if missing_reservations :
                parts .append ("已补入遗漏的保留条件")
            rationale_appendix ="；".join (parts )+"。"

        reviews .append (
        JudgementReview (
        issue_id =judgement .issue_id ,
        passed =not invalid_cited_claim_ids and not missing_reservations ,
        extra_conditions =_dedupe (extra_conditions ),
        rationale_appendix =rationale_appendix ,
        invalid_cited_claim_ids =invalid_cited_claim_ids ,
        missing_reservations =missing_reservations ,
        )
        )

    return reviews 

def apply_judgement_reviews (
judgements :list [Judgement ],
reviews :list [JudgementReview ],
)->list [Judgement ]:
    review_index ={review .issue_id :review for review in reviews }
    merged :list [Judgement ]=[]

    for judgement in judgements :
        review =review_index .get (judgement .issue_id )
        if review is None :
            merged .append (judgement )
            continue 

        cited_claim_ids =[
        claim_id for claim_id in judgement .cited_claim_ids if claim_id not in set (review .invalid_cited_claim_ids )
        ]
        conditions =_merge_conditions (judgement .conditions ,review .extra_conditions )
        rationale =judgement .rationale 
        if review .rationale_appendix :
            rationale =rationale .rstrip ("。.")+"；复核："+review .rationale_appendix .rstrip ("。.")+"。"

        merged .append (
        Judgement (
        issue_id =judgement .issue_id ,
        disposition =judgement .disposition ,
        favored_system =judgement .favored_system ,
        rationale =rationale ,
        conditions =conditions ,
        cited_claim_ids =cited_claim_ids ,
        summary =judgement .summary ,
        verifier_status ="passed"if review .passed else "flagged",
        verifier_summary =review .rationale_appendix ,
        )
        )

    return merged 

def _decide (
issue :DebateIssue ,
top_system :str ,
top_score :float ,
second_score :float ,
claims :list [Claim ],
)->Tuple [JudgementDisposition ,Optional [str ],List [str ]]:
    conditions :list [str ]=[]

    if issue .relation ==ClaimRelation .CONSENSUS :
        return JudgementDisposition .MUTUAL_VALIDITY ,None ,conditions 
    if issue .relation ==ClaimRelation .INSUFFICIENT_DATA :
        conditions .append ("当前资料不足，建议补充出生时辰或更精确的出生地点")
        return JudgementDisposition .UNRESOLVED ,None ,conditions 

    if top_score ==second_score or issue .severity <0.55 :
        conditions .append ("双方证据差距不大，只能保留条件性判断")
        return JudgementDisposition .CONDITIONAL ,top_system ,conditions 

    favored_disposition =JudgementDisposition .FAVOR_A if top_system ==claims [0 ].system else JudgementDisposition .FAVOR_B 
    return favored_disposition ,top_system ,conditions 

def _build_rationale (
issue :DebateIssue ,
claims :list [Claim ],
rebuttals :list [Rebuttal ],
disposition :JudgementDisposition ,
favored_system :Optional [str ],
conditions :list [str ],
)->str :
    dimension_label =_dimension_label (issue .dimension )
    favored_label =_system_label (favored_system )if favored_system else None 
    claim_ids =", ".join (claim .claim_id for claim in claims )
    rebuttal_hint =(
    "; ".join (rebuttal .summary_hint or rebuttal .response for rebuttal in rebuttals [:2 ])
    if rebuttals 
    else "无额外质询回应"
    )
    rebuttal_hint =rebuttal_hint .rstrip ("。.")
    detail_hint =rebuttal_hint 
    if conditions :
        detail_hint =f"{detail_hint}；条件：{'；'.join(conditions)}"

    if disposition ==JudgementDisposition .MUTUAL_VALIDITY :
        return (
        f"{dimension_label}维度的 claim [{claim_ids}] 已形成一致判断，"
        f"当前不需要单边裁决。{detail_hint}。"
        )
    if disposition ==JudgementDisposition .CONDITIONAL :
        return (
        f"{dimension_label}维度当前更偏向{favored_label}，"
        "但仍只在条件边界内成立；"
        f"依据 claim [{claim_ids}]。{detail_hint}。"
        )
    if disposition ==JudgementDisposition .UNRESOLVED :
        return (
        f"{dimension_label}维度仍未形成稳定裁决，"
        f"当前只能保守保留。依据 claim [{claim_ids}]。{detail_hint}。"
        )
    return (
    f"{dimension_label}维度当前更倾向{favored_label}，"
    "但仍保留不确定性；"
    f"依据 claim [{claim_ids}]。{detail_hint}。"
    )

def _system_scores (claims :list [Claim ])->dict [str ,float ]:
    scores :dict [str ,list [int ]]=defaultdict (list )
    for claim in claims :
        scores [claim .system ].append (len (claim .statement )+len (claim .evidence ))
    return {system :round (sum (values )/len (values ),2 )for system ,values in scores .items ()}

def _summarize_judgement (
issue :DebateIssue ,
disposition :JudgementDisposition ,
favored_system :Optional [str ],
)->str :
    dimension_label =_dimension_label (issue .dimension )
    if disposition ==JudgementDisposition .MUTUAL_VALIDITY :
        return f"{dimension_label}维度当前以稳定共识为主。"
    if disposition ==JudgementDisposition .CONDITIONAL :
        return f"{dimension_label}维度当前只能给出条件性判断。"
    if disposition ==JudgementDisposition .UNRESOLVED :
        return f"{dimension_label}维度当前仍无法终局。"
    return f"{dimension_label}维度当前更偏向{_system_label(favored_system)}。"

def _battle_conditions (issue :DebateIssue )->list [str ]:
    if issue .termination_reason =="max-rounds-reached":
        return [f"该 issue 已完成 {issue.rounds_completed} 轮对辩仍未互相说服，最终由裁判终局"]
    if issue .termination_reason =="stability-stop":
        return [f"该 issue 在最近两个完整回合内没有新增有效进展，已提前结束并交由裁判终局"]
    if issue .termination_reason =="single-sided-issue":
        return ["该 issue 只有单侧体系可继续答辩，未形成实质性多方对辩"]
    if issue .termination_reason =="mutual-convergence":
        return [f"对辩进行到第 {issue.rounds_completed} 轮后，双方分歧已明显收敛"]
    if issue .termination_reason =="model-round-failed":
        return ["某一轮对辩未返回有效文本，已提前交给裁判终局"]
    return []

def _required_reservations (issue :DebateIssue )->list [str ]:
    required =_battle_conditions (issue )
    if issue .relation ==ClaimRelation .INSUFFICIENT_DATA :
        required .append ("当前资料不足，建议补充出生时辰或更精确的出生地点")
    return _dedupe (required )

def _has_matching_condition (existing_conditions :list [str ],required_condition :str )->bool :
    return any (condition ==required_condition for condition in existing_conditions )

def _merge_conditions (primary :list [str ],extra :list [str ])->list [str ]:
    merged =list (primary )
    for item in extra :
        if item not in merged :
            merged .append (item )
    return merged 

def _claim_index (evidence_list :list [SystemEvidence ])->dict [str ,Claim ]:
    index :dict [str ,Claim ]={}
    for evidence in evidence_list :
        for claim in evidence .claims :
            index [claim .claim_id ]=claim 
    return index 

def _rebuttal_index (rebuttals :list [Rebuttal ])->dict [str ,list [Rebuttal ]]:
    index :dict [str ,list [Rebuttal ]]=defaultdict (list )
    for rebuttal in rebuttals :
        index [rebuttal .issue_id ].append (rebuttal )
    return index 

def _dedupe (items :list [str ])->list [str ]:
    seen :set [str ]=set ()
    ordered :list [str ]=[]
    for item in items :
        if item not in seen :
            seen .add (item )
            ordered .append (item )
    return ordered 

def _system_label (system :Optional [str ])->Optional [str ]:
    if system is None :
        return None 
    return _SYSTEM_LABELS .get (system ,system )

def _dimension_label (dimension :str )->str :
    return _DIMENSION_LABELS .get (dimension ,dimension )
