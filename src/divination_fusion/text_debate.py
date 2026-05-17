from __future__ import annotations 

from hashlib import sha1 
import re 
from typing import Any 

from divination_fusion .models import ClaimRelation ,DebateIssue ,JudgementDisposition ,Rebuttal ,SystemEvidence 
from divination_fusion .prompts import _load 

_DIMENSION_ALIASES ={
"career":"career",
"事业":"career",
"relationship":"relationship",
"感情":"relationship",
"personality":"personality",
"性格":"personality",
"risk":"risk",
"风险":"risk",
"wealth":"wealth",
"财务":"wealth",
"财运":"wealth",
"health":"health",
"健康":"health",
}

def analyzer_user_prompt (query :str ,focus_areas :list [str ],normalized_profile :dict [str ,Any ])->str :
    return _load (
    "user_analyzer_fallback",
    query =query ,
    focus_areas ="、".join (focus_areas )if focus_areas else "未显式指定",
    normalized_profile =str (normalized_profile ),
    )

def judge_issue_user_prompt (query :str ,evidence_list :list [SystemEvidence ])->str :
    system_text ="\n\n".join (
    [
    f"【{evidence.system.upper()} 分析文本】\n{evidence.analysis_text or evidence.summary}"
    for evidence in evidence_list 
    ]
    )
    return _load (
    "user_judge_issue",
    query =query ,
    system_text =system_text ,
    )

def battler_user_prompt (
*,
query :str ,
issue :DebateIssue ,
system_name :str ,
own_analysis :str ,
opponent_analysis :str ,
prior_rebuttals :list [Rebuttal ],
judge_question :str ,
)->str :
    transcript ="\n\n".join (
    [
    f"第 {item.round_index} 轮 {item.system}：{item.public_response or item.response}"
    for item in prior_rebuttals [-6 :]
    ]
    )or "暂无历史争论。"
    opponent ="ziwei"if system_name =="bazi"else "bazi"
    return _load (
    "user_battler_round",
    query =query ,
    issue_title =issue .title or issue .question ,
    scope_note =issue .scope_note or "只围绕当前争点，不要扩展",
    judge_question =judge_question ,
    own_analysis =own_analysis ,
    opponent_analysis =opponent_analysis ,
    transcript =transcript ,
    system_name =system_name ,
    opponent =opponent ,
    )

def judge_round_user_prompt (
*,
query :str ,
issue :DebateIssue ,
prior_rebuttals :list [Rebuttal ],
current_round :list [Rebuttal ],
)->str :
    history ="\n\n".join (
    [
    f"第 {item.round_index} 轮 {item.system}：{item.public_response or item.response}"
    for item in prior_rebuttals [-8 :]
    ]
    )or "暂无历史争论。"
    latest ="\n\n".join (
    [
    f"{item.system}：{item.public_response or item.response}"
    for item in current_round 
    ]
    )
    return _load (
    "user_judge_round",
    query =query ,
    issue_title =issue .title or issue .question ,
    scope_note =issue .scope_note or "只围绕当前争点",
    issue_question =issue .question ,
    history =history ,
    latest =latest ,
    )

def judge_final_user_prompt (
*,
query :str ,
issue :DebateIssue ,
evidence_list :list [SystemEvidence ],
rebuttals :list [Rebuttal ],
)->str :
    system_text ="\n\n".join (
    [
    f"【{item.system.upper()} 原始分析】\n{item.analysis_text or item.summary}"
    for item in evidence_list 
    ]
    )
    transcript ="\n\n".join (
    [
    f"第 {item.round_index} 轮 {item.system}：{item.public_response or item.response}"
    for item in rebuttals 
    ]
    )or "双方没有形成有效争论。"
    return _load (
    "user_judge_final",
    query =query ,
    issue_title =issue .title or issue .question ,
    scope_note =issue .scope_note or "只围绕当前争点",
    system_text =system_text ,
    transcript =transcript ,
    )

def extract_summary (text :str )->str :
    summary =extract_section (text ,"结论")
    if summary :
        return summary 
    compact =[line .strip ()for line in text .splitlines ()if line .strip ()]
    return compact [0 ]if compact else ""

def extract_section (text :str ,title :str )->str :
    pattern =rf"【{re.escape(title)}】\s*(.*?)(?=\n【|\Z)"
    match =re .search (pattern ,text ,re .S )
    return match .group (1 ).strip ()if match else ""

def parse_issue_text (raw_text :str ,focus_areas :list [str ])->list [DebateIssue ]:
    text =raw_text .strip ()
    if not text or "无需要争论的议题"in text :
        return []
    blocks =re .split (r"(?=\[议题\d+\])",text )
    issues :list [DebateIssue ]=[]
    for block in blocks :
        block =block .strip ()
        if not block :
            continue 
        dimension =_normalize_dimension (_line_value (block ,"维度"),focus_areas )
        title =_line_value (block ,"标题")or f"{dimension} 争点"
        relation =_parse_relation (_line_value (block ,"关系"))
        bazi_view =_line_value (block ,"八字立场")
        astro_view =_line_value (block ,"紫微立场")
        question =_line_value (block ,"裁判发问")or title 
        scope_note =_line_value (block ,"控题边界")
        issue_id =_stable_id ("issue",dimension ,title ,bazi_view ,astro_view )
        issues .append (
        DebateIssue (
        issue_id =issue_id ,
        dimension =dimension ,
        relation =relation ,
        claim_ids =[],
        question =question ,
        severity =_severity_for_relation (relation ),
        title =title ,
        system_views ={"bazi":bazi_view ,"ziwei":astro_view },
        scope_note =scope_note or None ,
        )
        )
    return issues 

def parse_round_control (raw_text :str )->dict [str ,str ]:
    return {
    "status":_normalize_status (_line_value (raw_text ,"当前状态")),
    "moderation":_line_value (raw_text ,"裁判意见"),
    "next_question":_line_value (raw_text ,"下一轮问题"),
    "termination_reason":_line_value (raw_text ,"终止原因"),
    }

def parse_final_judgement (raw_text :str )->dict [str ,Any ]:
    conditions =re .findall (r"^\s*-\s*(.+)$",raw_text ,re .M )
    return {
    "disposition":_normalize_disposition (_line_value (raw_text ,"裁决类型")),
    "favored_system":_normalize_system_name (_line_value (raw_text ,"偏向体系")),
    "summary":_line_value (raw_text ,"裁决摘要"),
    "rationale":_line_value (raw_text ,"裁决理由"),
    "conditions":[item .strip ()for item in conditions if item .strip ()],
    }

def local_issue_fallback (evidence_list :list [SystemEvidence ],focus_areas :list [str ])->list [DebateIssue ]:
    texts ={item .system :item .analysis_text or item .summary for item in evidence_list }
    populated ={system :value for system ,value in texts .items ()if value .strip ()}
    if not populated :
        return []
    if len (populated )==1 :
        dimension =_normalize_dimension (focus_areas [0 ]if focus_areas else "career",focus_areas )
        title =f"{dimension} 维度暂时只有单侧分析"
        issue_id =_stable_id ("issue",dimension ,*populated .values ())
        return [
        DebateIssue (
        issue_id =issue_id ,
        dimension =dimension ,
        relation =ClaimRelation .INSUFFICIENT_DATA ,
        claim_ids =[],
        question =f"当前只有单侧流派文本，是否需要等待另一侧补齐后再争论？",
        severity =0.4 ,
        title =title ,
        system_views =texts ,
        scope_note =f"只围绕{title}说明当前无法形成正式争论。",
        )
        ]
    if len (set (populated .values ()))<=1 :
        return []
    dimension =_normalize_dimension (focus_areas [0 ]if focus_areas else "career",focus_areas )
    title =f"{dimension} 维度存在解释分歧"
    issue_id =_stable_id ("issue",dimension ,texts .get ("bazi",""),texts .get ("ziwei",""))
    return [
    DebateIssue (
    issue_id =issue_id ,
    dimension =dimension ,
    relation =ClaimRelation .TENSION ,
    claim_ids =[],
    question =f"围绕{title}继续争论，并直接回应对方。",
    severity =0.6 ,
    title =title ,
    system_views =texts ,
    scope_note =f"只讨论{title}，不要扩展到别的话题。",
    )
    ]

def local_judgement_fallback (issue :DebateIssue ,rebuttals :list [Rebuttal ])->tuple [JudgementDisposition ,str |None ,str ,list [str ],str ]:
    if not rebuttals :
        return (
        JudgementDisposition .UNRESOLVED ,
        None ,
        "当前没有形成有效争论文本，暂时无法裁决。",
        ["模型裁判未能返回有效文本，当前先保留未决。"],
        "当前无法终局。",
        )
    last =rebuttals [-1 ]
    favored =last .system if last .system in {"bazi","ziwei"}else None 
    return (
    JudgementDisposition .CONDITIONAL ,
    favored ,
    f"模型裁判未能返回有效文本，当前先按最后一轮回应保守保留；最近一轮来自 {last.system}，但这不构成硬判。",
    ["模型裁判失败，当前结果仅作保守参考。"],
    "当前只能给出保守性判断。",
    )

def _line_value (text :str ,label :str )->str :
    pattern =(
    rf"^\s*{re.escape(label)}[：:]\s*(.*?)\s*"
    rf"(?=^\s*(?:[^\[\]\n]+)[：:]|\Z)"
    )
    match =re .search (pattern ,text ,re .M |re .S )
    if not match :
        return ""
    return match .group (1 ).strip ()

def _normalize_dimension (value :str ,focus_areas :list [str ])->str :
    key =value .strip ().lower ()
    if key in _DIMENSION_ALIASES :
        return _DIMENSION_ALIASES [key ]
    if focus_areas :
        return focus_areas [0 ]
    return "career"

def _parse_relation (value :str )->ClaimRelation :
    normalized =value .strip ().lower ()
    if normalized =="contradiction":
        return ClaimRelation .CONTRADICTION 
    if normalized =="insufficient-data":
        return ClaimRelation .INSUFFICIENT_DATA 
    return ClaimRelation .TENSION 

def _normalize_status (value :str )->str :
    value =value .strip ()
    if not value :
        return "继续"
    if any (token in value for token in ("结束","停止","终局","收束","无需继续")):
        return "结束"
    return "继续"

def _normalize_disposition (value :str )->JudgementDisposition :
    value =value .strip ().lower ()
    mapping ={
    "favor-a":JudgementDisposition .FAVOR_A ,
    "favor-b":JudgementDisposition .FAVOR_B ,
    "conditional":JudgementDisposition .CONDITIONAL ,
    "unresolved":JudgementDisposition .UNRESOLVED ,
    "mutual-validity":JudgementDisposition .MUTUAL_VALIDITY ,
    }
    return mapping .get (value ,JudgementDisposition .UNRESOLVED )

def _normalize_system_name (value :str )->str |None :
    normalized =value .strip ().lower ()
    if normalized in {"bazi","ziwei"}:
        return normalized 
    return None 

def _severity_for_relation (relation :ClaimRelation )->float :
    if relation ==ClaimRelation .CONTRADICTION :
        return 0.8 
    if relation ==ClaimRelation .INSUFFICIENT_DATA :
        return 0.4 
    return 0.6 

def _stable_id (prefix :str ,*parts :str )->str :
    digest =sha1 ("|".join (parts ).encode ("utf-8")).hexdigest ()[:10 ]
    return f"{prefix}_{digest}"
