from __future__ import annotations 

from collections import OrderedDict 

from divination_fusion .models import (
AnalysisRequest ,
DebateIssue ,
FusionReport ,
Judgement ,
JudgementDisposition ,
NormalizedProfile ,
SystemEvidence ,
)

_MISSING_FIELD_LABELS ={
"birth_date":"出生日期",
"birth_time":"出生时辰",
"birth_place":"出生地点",
"timezone":"时区",
}

_DIMENSION_LABELS ={
"career":"事业",
"personality":"性格",
"relationship":"感情",
"risk":"风险",
"health":"健康",
"wealth":"财务",
}

def synthesize_report (
request :AnalysisRequest ,
profile :NormalizedProfile ,
evidence_list :list [SystemEvidence ],
judgements :list [Judgement ],
issues :list [DebateIssue ],
)->FusionReport :
    consensus_points =_consensus_points (judgements ,evidence_list )
    disagreement_points =_disagreement_points (judgements ,issues )
    reservations =_reservations (profile ,evidence_list ,judgements ,issues )
    suggested_followups =_followups (profile ,issues ,judgements )
    summary =_summary (request ,profile ,judgements )

    raw_sections =OrderedDict (
    [
    ("结论摘要",summary ),
    ("共识",consensus_points ),
    ("分歧",disagreement_points ),
    ("保留意见",reservations ),
    ("建议补充资料",suggested_followups ),
    ("可继续追问点",[issue .question for issue in issues ]),
    ]
    )
    return FusionReport (
    summary =summary ,
    consensus_points =consensus_points ,
    disagreement_points =disagreement_points ,
    reservations =reservations ,
    suggested_followups =suggested_followups ,
    raw_sections =dict (raw_sections ),
    )

def _summary (request :AnalysisRequest ,profile :NormalizedProfile ,judgements :list [Judgement ])->str :
    missing_fields =_humanize_missing_fields (profile .missing_fields )
    missing_suffix =f" 仍缺少{missing_fields}，结论需结合补充资料阅读。"if missing_fields else ""
    if not judgements :
        if missing_fields :
            return f"针对“{request.query}”，当前仍缺少{missing_fields}，先给出保守版判断。"
        return f"针对“{request.query}”，当前资料不足，先给出保守版判断。"
    counts =_judgement_counts (judgements )
    stable =counts [JudgementDisposition .MUTUAL_VALIDITY .value ]
    conditional =counts [JudgementDisposition .CONDITIONAL .value ]
    unresolved =counts [JudgementDisposition .UNRESOLVED .value ]
    favored =counts [JudgementDisposition .FAVOR_A .value ]+counts [JudgementDisposition .FAVOR_B .value ]

    summary_parts :list [str ]=[]
    if stable :
        summary_parts .append (f"{stable} 个稳定共识")
    if conditional :
        summary_parts .append (f"{conditional} 个条件性判断")
    if favored :
        summary_parts .append (f"{favored} 个偏向性判断")
    if unresolved :
        summary_parts .append (f"{unresolved} 个未决项")

    if summary_parts :
        if stable and not (conditional or unresolved or favored ):
            lead =f"针对“{request.query}”，当前结果以稳定共识为主。"
        elif conditional and not stable and not favored :
            lead =f"针对“{request.query}”，当前结果以条件性判断为主，尚未形成完全稳定的共识。"
            if unresolved :
                lead +=f" 另有 {unresolved} 个未决项需要补充资料。"
        elif favored and not stable and not conditional :
            lead =f"针对“{request.query}”，当前结果以偏向性判断为主，但仍保留不确定性。"
            if unresolved :
                lead +=f" 另有 {unresolved} 个未决项需要补充资料。"
        else :
            lead =f"针对“{request.query}”，当前结果包含 { '、'.join(summary_parts) }。"
    else :
        lead =f"针对“{request.query}”，当前结果仍以保守判断为主。"

    return lead +missing_suffix 

def _consensus_points (judgements :list [Judgement ],evidence_list :list [SystemEvidence ])->list [str ]:
    points :list [str ]=[]
    for judgement in judgements :
        if judgement .disposition .value ==JudgementDisposition .MUTUAL_VALIDITY .value :
            points .append (f"{judgement.issue_id}：{judgement.rationale}")
    if not points :
        points .append ("各体系在当前资料下未形成稳定共识。")
    return points 

def _disagreement_points (judgements :list [Judgement ],issues :list [DebateIssue ])->list [str ]:
    issue_map ={issue .issue_id :issue for issue in issues }
    points :list [str ]=[]
    for judgement in judgements :
        if judgement .disposition .value in {
        JudgementDisposition .FAVOR_A .value ,
        JudgementDisposition .FAVOR_B .value ,
        JudgementDisposition .CONDITIONAL .value ,
        JudgementDisposition .UNRESOLVED .value ,
        }:
            issue =issue_map .get (judgement .issue_id )
            label =_dimension_label (issue .dimension )if issue else judgement .issue_id 
            points .append (f"{label}：{judgement.rationale}")
    if not points :
        points .append ("当前未发现需要重点区分的分歧。")
    return points 

def _reservations (
profile :NormalizedProfile ,
evidence_list :list [SystemEvidence ],
judgements :list [Judgement ],
issues :list [DebateIssue ],
)->list [str ]:
    reservations =list (profile .notes )
    if profile .missing_fields :
        reservations .append (
        f"当前资料仍缺少{_humanize_missing_fields(profile.missing_fields)}，相关结论应按保守口径理解。"
        )
    for evidence in evidence_list :
        reservations .extend (evidence .warnings )
    for judgement in judgements :
        if judgement .disposition .value ==JudgementDisposition .CONDITIONAL .value :
            reservations .append (f"{judgement.issue_id} 对应条件性结论，需连同适用前提一起阅读。")
    if any (judgement .disposition .value =="unresolved"for judgement in judgements ):
        reservations .append ("存在无法裁决的 issue，结论需与补充资料一起阅读。")
    for issue in issues :
        if issue .termination_reason =="max-rounds-reached":
            reservations .append (
            f"{_dimension_label(issue.dimension)}维度已完成 {issue.rounds_completed} 轮对辩仍未互相说服，最后由裁判终局。"
            )
        if issue .termination_reason =="stability-stop":
            reservations .append (
            f"{_dimension_label(issue.dimension)}维度在最近两个完整回合内没有新增有效进展，已提前结束并交给裁判终局。"
            )
    return _dedupe (reservations )or ["当前保留意见较少，但仍建议结合现实情境理解。"]

def _followups (profile :NormalizedProfile ,issues :list [DebateIssue ],judgements :list [Judgement ])->list [str ]:
    issue_map ={issue .issue_id :issue for issue in issues }
    followups :list [str ]=[]
    if profile .missing_fields :
        followups .append (
        f"优先补充{_humanize_missing_fields(profile.missing_fields)}，这些信息会直接影响归一化与裁决精度。"
        )
    for issue in issues :
        if issue .status =="open":
            followups .append (f"继续追问{_dimension_label(issue.dimension)}维度：{issue.question}")
    for judgement in judgements :
        if judgement .disposition .value ==JudgementDisposition .CONDITIONAL .value :
            issue =issue_map .get (judgement .issue_id )
            label =_dimension_label (issue .dimension )if issue else judgement .issue_id 
            followups .append (f"继续确认{label}维度的适用前提与条件边界。")
    return _dedupe (followups )or ["可继续追问当前结论对应的条件边界。"]

def _humanize_missing_fields (fields :list [str ])->str :
    labels =[_MISSING_FIELD_LABELS .get (field ,field )for field in fields ]
    return "、".join (labels )

def _dedupe (items :list [str ])->list [str ]:
    seen :set [str ]=set ()
    ordered :list [str ]=[]
    for item in items :
        if item not in seen :
            seen .add (item )
            ordered .append (item )
    return ordered 

def _judgement_counts (judgements :list [Judgement ])->dict [str ,int ]:
    counts :dict [str ,int ]={
    disposition .value :0 for disposition in JudgementDisposition 
    }
    for judgement in judgements :
        counts [judgement .disposition .value ]+=1 
    return counts 

def _dimension_label (dimension :str )->str :
    return _DIMENSION_LABELS .get (dimension ,dimension )
