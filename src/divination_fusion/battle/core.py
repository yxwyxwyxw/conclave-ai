from __future__ import annotations 

from collections import defaultdict 
from hashlib import sha1 
import re 
from typing import Iterable 

from divination_fusion .models import (
Claim ,
ClaimRelation ,
CrossExamQuestion ,
DebateIssue ,
MappedDimension ,
Rebuttal ,
SystemEvidence ,
)

DEFAULT_MAX_BATTLE_ROUNDS =6 
HARD_MAX_BATTLE_ROUNDS =50 

_OPPOSING_PAIRS :tuple [tuple [str ,str ],...]=(
("strong","weak"),
("stable","volatile"),
("growth","decline"),
("support","challenge"),
("opportunity","risk"),
("open","closed"),
("expansive","constrained"),
("favorable","unfavorable"),
("favourable","unfavourable"),
)

_CONSENSUS_MARKERS ={
"same",
"similar",
"shared",
"consistent",
"aligned",
"convergent",
}

_INSUFFICIENT_MARKERS ={
"uncertain",
"limited",
"low data",
"missing",
"unknown",
"tentative",
"不足",
"缺失",
"保守",
"暂定",
}

_LOW_SIGNAL_TOKENS ={
"当前",
"条件",
"判断",
"结论",
"资料",
"建议",
"适合",
"需要",
"更容",
"容易",
}

_SYSTEM_LABELS ={
"bazi":"八字",
"astrology":"星盘",
"ziwei":"紫微",
"unknown":"未知体系",
}

_DIMENSION_LABELS ={
"career":"事业",
"personality":"性格",
"relationship":"感情",
"risk":"风险",
"health":"健康",
"wealth":"财务",
}

def map_dimensions (evidence_list :list [SystemEvidence ])->list [MappedDimension ]:
    dimension_claims :dict [str ,dict [str ,list [str ]]]=defaultdict (lambda :defaultdict (list ))
    dimension_notes :dict [str ,list [str ]]=defaultdict (list )

    for evidence in evidence_list :
        for claim in evidence .claims :
            dimension_claims [claim .dimension ][claim .system ].append (claim .claim_id )
        if evidence .warnings :
            for claim in evidence .claims :
                dimension_notes [claim .dimension ].extend (
                f"{evidence.system}: {warning}"for warning in evidence .warnings 
                )

    mapped :list [MappedDimension ]=[]
    for dimension in sorted (dimension_claims ):
        system_claim_ids ={
        system :sorted (ids )
        for system ,ids in sorted (dimension_claims [dimension ].items ())
        }
        mapped .append (
        MappedDimension (
        dimension =dimension ,
        system_claim_ids =system_claim_ids ,
        notes =_dedupe_preserve_order (dimension_notes .get (dimension ,[])),
        )
        )
    return mapped 

def detect_debate_issues (
evidence_list :list [SystemEvidence ],
mapped_dimensions :list [MappedDimension ],
)->list [DebateIssue ]:
    claim_index =_claim_index (evidence_list )
    issues :list [DebateIssue ]=[]

    for mapped in mapped_dimensions :
        claims =_claims_for_dimension (claim_index .values (),mapped .dimension )
        if not claims :
            continue 

        relation =_infer_relation (claims )
        if relation ==ClaimRelation .CONSENSUS :
            continue 

        issue_id =_stable_id ("issue",mapped .dimension ,relation .value ,*sorted (claim .claim_id for claim in claims ))
        severity =_severity_for_issue (relation ,claims )
        question =_issue_question (mapped .dimension ,relation ,claims )
        issues .append (
        DebateIssue (
        issue_id =issue_id ,
        dimension =mapped .dimension ,
        relation =relation ,
        claim_ids =sorted (claim .claim_id for claim in claims ),
        question =question ,
        severity =severity ,
        status ="open"if severity >0 else "closed",
        )
        )

    return sorted (issues ,key =lambda issue :(-issue .severity ,issue .dimension ,issue .issue_id ))

def build_cross_exam_questions (
issues :list [DebateIssue ],
evidence_list :list [SystemEvidence ],
*,
rebuttals :list [Rebuttal ]|None =None ,
round_index :int =1 ,
)->list [CrossExamQuestion ]:
    claim_index =_claim_index (evidence_list )
    questions :list [CrossExamQuestion ]=[]
    transcript =rebuttals or []

    for issue in issues :
        issue_claims =[claim_index [claim_id ]for claim_id in issue .claim_ids if claim_id in claim_index ]
        target_system =_target_system_for_issue (issue_claims ,transcript ,issue .issue_id )

        prompt =_question_prompt (issue ,issue_claims ,target_system )
        rationale =_question_rationale (issue ,issue_claims ,transcript ,issue .issue_id ,round_index )
        questions .append (
        CrossExamQuestion (
        issue_id =issue .issue_id ,
        round_index =round_index ,
        target_system =target_system ,
        prompt =prompt ,
        rationale =rationale ,
        )
        )

    return questions 

def build_rebuttals (
questions :list [CrossExamQuestion ],
issues :list [DebateIssue ],
evidence_list :list [SystemEvidence ],
*,
rebuttals :list [Rebuttal ]|None =None ,
)->list [Rebuttal ]:
    claim_index =_claim_index (evidence_list )
    issue_index ={issue .issue_id :issue for issue in issues }
    built_rebuttals :list [Rebuttal ]=[]
    transcript =rebuttals or []

    for question in questions :
        issue =issue_index .get (question .issue_id )
        target_claims =_target_claims_for_issue (question ,issue ,claim_index )
        best_claims =_best_claims_for_issue (target_claims )
        issue_rebuttals =_issue_rebuttals (transcript ,question .issue_id )
        response =_rebuttal_response (question ,issue ,best_claims ,issue_rebuttals )
        public_response =_public_rebuttal_response (question ,issue ,best_claims ,issue_rebuttals )
        built_rebuttals .append (
        Rebuttal (
        issue_id =question .issue_id ,
        round_index =question .round_index ,
        system =question .target_system ,
        response =response ,
        public_response =public_response ,
        supported_claim_ids =[claim .claim_id for claim in best_claims ],
        argument_points =[claim .statement for claim in best_claims ],
        new_argument_points =[],
        summary_hint =response ,
        )
        )

    return built_rebuttals 

def run_battle (
issues :list [DebateIssue ],
evidence_list :list [SystemEvidence ],
*,
max_rounds :int =DEFAULT_MAX_BATTLE_ROUNDS ,
)->tuple [list [CrossExamQuestion ],list [Rebuttal ]]:
    normalized_max_rounds =normalize_max_battle_rounds (max_rounds )
    claim_index =_claim_index (evidence_list )
    all_questions :list [CrossExamQuestion ]=[]
    all_rebuttals :list [Rebuttal ]=[]

    for issue in issues :
        issue .status ="open"
        issue .rounds_completed =0 
        issue .termination_reason =None 
        issue .summary =None 
        issue .stability_status =None 
        issue .stability_summary =None 

        issue_claims =[claim_index [claim_id ]for claim_id in issue .claim_ids if claim_id in claim_index ]
        for round_index in range (1 ,normalized_max_rounds +1 ):
            questions =build_cross_exam_questions (
            [issue ],
            evidence_list ,
            rebuttals =all_rebuttals ,
            round_index =round_index ,
            )
            if not questions :
                break 
            round_rebuttals =build_rebuttals (
            questions ,
            [issue ],
            evidence_list ,
            rebuttals =all_rebuttals ,
            )
            all_questions .extend (questions )
            all_rebuttals .extend (round_rebuttals )
            issue .rounds_completed =round_index 

            should_stop ,reason ,status =_should_stop_issue (
            issue ,
            issue_claims ,
            _issue_rebuttals (all_rebuttals ,issue .issue_id ),
            normalized_max_rounds ,
            )
            if should_stop :
                issue .termination_reason =reason 
                if status :
                    issue .status =status 
                if reason =="stability-stop":
                    issue .stability_status ="stalled"
                    issue .stability_summary =(
                    f"{_dimension_label(issue.dimension)}维度最近两个完整回合没有新增有效进展，已提前结束。"
                    )
                    issue .summary =issue .stability_summary 
                elif reason =="mutual-convergence":
                    issue .summary =f"{_dimension_label(issue.dimension)}维度在第 {issue.rounds_completed} 轮后收敛。"
                elif reason =="single-sided-issue":
                    issue .summary =f"{_dimension_label(issue.dimension)}维度只有单侧证据，未进入多方对辩。"
                break 

        if issue .rounds_completed >=normalized_max_rounds and issue .termination_reason is None :
            issue .termination_reason ="max-rounds-reached"
        if issue .termination_reason =="max-rounds-reached":
            issue .summary =f"{_dimension_label(issue.dimension)}维度达到轮数上限，转入裁判终局。"

    return all_questions ,all_rebuttals 

def normalize_max_battle_rounds (value :object )->int :
    if value in (None ,""):
        return DEFAULT_MAX_BATTLE_ROUNDS 
    try :
        parsed =int (value )
    except (TypeError ,ValueError )as exc :
        raise ValueError ("max_battle_rounds 必须是整数。")from exc 
    if parsed <1 :
        raise ValueError ("max_battle_rounds 必须大于 0。")
    if parsed >HARD_MAX_BATTLE_ROUNDS :
        return HARD_MAX_BATTLE_ROUNDS 
    return parsed 

def _claim_index (evidence_list :Iterable [SystemEvidence ])->dict [str ,Claim ]:
    index :dict [str ,Claim ]={}
    for evidence in evidence_list :
        for claim in evidence .claims :
            index [claim .claim_id ]=claim 
    return index 

def _claims_for_dimension (claims :Iterable [Claim ],dimension :str )->list [Claim ]:
    return [claim for claim in claims if claim .dimension ==dimension ]

def _infer_relation (claims :list [Claim ])->ClaimRelation :
    if len (claims )<2 :
        return ClaimRelation .INSUFFICIENT_DATA 

    statements =[claim .statement for claim in claims ]
    if any (_has_insufficient_marker (text )for text in statements ):
        return ClaimRelation .INSUFFICIENT_DATA 
    if _claims_align (statements ):
        return ClaimRelation .CONSENSUS 
    if _claims_conflict (statements ):
        return ClaimRelation .CONTRADICTION 
    if _shared_claim_keywords (statements ):
        return ClaimRelation .TENSION 
    if len ({_normalize_text (statement )for statement in statements })>1 :
        return ClaimRelation .TENSION 
    return ClaimRelation .CONSENSUS 

def _severity_for_issue (relation :ClaimRelation ,claims :list [Claim ])->float :
    if relation ==ClaimRelation .CONTRADICTION :
        return 0.8 
    if relation ==ClaimRelation .TENSION :
        return 0.6 
    if relation ==ClaimRelation .INSUFFICIENT_DATA :
        return 0.4 
    return 0.0 

def _issue_question (dimension :str ,relation :ClaimRelation ,claims :list [Claim ])->str :
    systems ="、".join (sorted ({_system_label (claim .system )for claim in claims }))
    dimension_label =_dimension_label (dimension )
    if relation ==ClaimRelation .CONTRADICTION :
        return f"{systems}在{dimension_label}维度给出了相互冲突的判断，哪一侧更受现有证据支持？"
    if relation ==ClaimRelation .TENSION :
        return f"{systems}在{dimension_label}维度存在张力，哪些现实条件会决定最终偏向？"
    return f"{dimension_label}维度的资料仍不足，是否存在缺失字段导致暂时无法裁决？"

def _question_prompt (issue :DebateIssue ,claims :list [Claim ],target_system :str )->str :
    claim_ids =", ".join (claim .claim_id for claim in claims )
    return (
    f"围绕 issue {issue.issue_id}（{_dimension_label(issue.dimension)} / {issue.relation.value}）展开当前轮对辩，"
    f"请从{_system_label(target_system)}的角度回应这些 claim: {claim_ids}。"
    "只允许引用该 issue 已出现的 claim，不要引入新的盘面事实。"
    )

def _question_rationale (
issue :DebateIssue ,
claims :list [Claim ],
rebuttals :list [Rebuttal ],
issue_id :str ,
round_index :int ,
)->str :
    previous_rounds =len (_issue_rebuttals (rebuttals ,issue_id ))
    return (
    f"当前进入第 {round_index} 轮对辩；该问题被标记为 {issue.relation.value}，"
    f"目的是检验{_dimension_label(issue.dimension)}维度上的核心分歧是否已经被回应；"
    f"此前已完成 {previous_rounds} 轮回应。"
    )

def _best_claims_for_issue (claims :list [Claim ])->list [Claim ]:
    if not claims :
        return []
    ranked =sorted (claims ,key =lambda claim :claim .claim_id )
    return ranked [:2 ]

def _target_claims_for_issue (
question :CrossExamQuestion ,
issue :DebateIssue |None ,
claim_index :dict [str ,Claim ],
)->list [Claim ]:
    if issue is None :
        return []
    return [
    claim_index [claim_id ]
    for claim_id in issue .claim_ids 
    if claim_id in claim_index and claim_index [claim_id ].system ==question .target_system 
    ]

def _target_system_for_issue (
claims :list [Claim ],
rebuttals :list [Rebuttal ],
issue_id :str ,
)->str :
    if not claims :
        return "unknown"

    grouped :dict [str ,list [Claim ]]=defaultdict (list )
    for claim in claims :
        grouped [claim .system ].append (claim )

    ranked =sorted (
    grouped .items (),
    key =lambda item :(
    len (item [1 ]),
    item [0 ],
    ),
    )
    ordered_systems =[system for system ,_claims in ranked ]
    previous_rounds =_issue_rebuttals (rebuttals ,issue_id )
    if not previous_rounds :
        return ordered_systems [0 ]
    last_system =previous_rounds [-1 ].system 
    if last_system not in ordered_systems :
        return ordered_systems [0 ]
    next_index =(ordered_systems .index (last_system )+1 )%len (ordered_systems )
    return ordered_systems [next_index ]

def _rebuttal_response (
question :CrossExamQuestion ,
issue :DebateIssue |None ,
best_claims :list [Claim ],
issue_rebuttals :list [Rebuttal ],
)->str :
    if issue is None or not best_claims :
        return (
        f"针对 issue {question.issue_id} 的第 {question.round_index} 轮，当前没有足够的同维度证据可直接回应，"
        "应回到该 issue 的输入完整度检查。"
        )
    claim_text ="; ".join (f"{claim.claim_id}：{claim.statement}"for claim in best_claims )
    support_summary =", ".join (claim .claim_id for claim in best_claims )
    previous =issue_rebuttals [-1 ]if issue_rebuttals else None 
    previous_hint =""
    if previous is not None :
        previous_claims =", ".join (previous .supported_claim_ids )or "无"
        previous_hint =(
        f" 第 {previous.round_index} 轮里，{_system_label(previous.system)}主要坚持的 claim 是 {previous_claims}。"
        )
    return (
    f"第 {question.round_index} 轮，仅就 issue {question.issue_id} 的{_dimension_label(issue.dimension)}维度而言，"
    f"{_system_label(question.target_system)}的主张仍由 {support_summary} 支持；"
    f"对应陈述为 {claim_text}。"
    f"{previous_hint}"
    "这只说明该 issue 范围内的证据尚未被推翻，"
    "不延伸到其他维度或其他 claim。"
    )

def _public_rebuttal_response (
question :CrossExamQuestion ,
issue :DebateIssue |None ,
best_claims :list [Claim ],
issue_rebuttals :list [Rebuttal ],
)->str :
    if issue is None or not best_claims :
        return (
        f"{_system_label(question.target_system)}在第 {question.round_index} 轮没有拿出新的同维度证据，"
        "当前更像是在提醒这条问题需要回到资料完整度检查。"
        )
    lead_claim =best_claims [0 ]
    previous =issue_rebuttals [-1 ]if issue_rebuttals else None 
    if previous is None :
        return (
        f"{_system_label(question.target_system)}认为，围绕{_dimension_label(issue.dimension)}这条争议，"
        f"现阶段最能支撑自身判断的仍是 {lead_claim.claim_id} 对应的证据链。"
        )
    return (
    f"{_system_label(question.target_system)}在第 {question.round_index} 轮继续坚持，"
    f"认为 {lead_claim.claim_id} 代表的判断还没有被上一轮真正推翻，"
    f"因此{_dimension_label(issue.dimension)}维度的核心分歧仍然成立。"
    )

def _should_stop_issue (
issue :DebateIssue ,
claims :list [Claim ],
rebuttals :list [Rebuttal ],
max_rounds :int ,
)->tuple [bool ,str |None ,str |None ]:
    systems =sorted ({claim .system for claim in claims })
    if len (systems )<2 :
        return True ,"single-sided-issue",None 

    if _rebuttals_converged (rebuttals ):
        return True ,"mutual-convergence","resolved"

    if issue .rounds_completed <max_rounds and _rebuttals_stalled (rebuttals ):
        return True ,"stability-stop",None 

    if issue .rounds_completed >=max_rounds :
        return True ,"max-rounds-reached",None 

    return False ,None ,None 

def _rebuttals_converged (rebuttals :list [Rebuttal ])->bool :
    if len (rebuttals )<2 :
        return False 
    latest =rebuttals [-1 ]
    previous =rebuttals [-2 ]
    return set (latest .supported_claim_ids )==set (previous .supported_claim_ids )

def _rebuttals_stalled (rebuttals :list [Rebuttal ])->bool :
    if len (rebuttals )<4 :
        return False 
    latest_four =rebuttals [-4 :]
    if len ({rebuttal .system for rebuttal in latest_four })<2 :
        return False 

    first_cycle =latest_four [:2 ]
    second_cycle =latest_four [2 :]
    first_by_system ={rebuttal .system :rebuttal for rebuttal in first_cycle }
    second_by_system ={rebuttal .system :rebuttal for rebuttal in second_cycle }
    if first_by_system .keys ()!=second_by_system .keys ():
        return False 

    for system ,earlier in first_by_system .items ():
        later =second_by_system [system ]
        if set (earlier .supported_claim_ids )!=set (later .supported_claim_ids ):
            return False 
        if set (earlier .still_disputed_points )!=set (later .still_disputed_points ):
            return False 
        if set (earlier .conceded_points )!=set (later .conceded_points ):
            return False 
        if getattr (earlier ,"new_argument_points",[])or getattr (later ,"new_argument_points",[]):
            return False 
        if earlier .stance !=later .stance :
            return False 
    return True 

def _issue_rebuttals (rebuttals :list [Rebuttal ],issue_id :str )->list [Rebuttal ]:
    return [rebuttal for rebuttal in rebuttals if rebuttal .issue_id ==issue_id ]

def _claims_align (statements :list [str ])->bool :
    if len (statements )<2 :
        return False 
    normalized =[_normalize_text (statement )for statement in statements ]
    if any (_contains_any (text ,_CONSENSUS_MARKERS )for text in normalized ):
        return True 
    shared =set (_signal_tokens (statements [0 ]))
    for text in statements [1 :]:
        shared &=set (_signal_tokens (text ))
    return len (shared )>=2 and not _claims_conflict (statements )

def _claims_conflict (statements :list [str ])->bool :
    normalized =[_normalize_text (statement )for statement in statements ]
    for text in normalized :
        for positive ,negative in _OPPOSING_PAIRS :
            if positive in text and negative in " ".join (normalized ):
                return True 
            if negative in text and positive in " ".join (normalized ):
                return True 
    return False 

def _shared_claim_keywords (statements :list [str ])->bool :
    shared =set (_signal_tokens (statements [0 ]))
    for text in statements [1 :]:
        shared &=set (_signal_tokens (text ))
    return len (shared )>=1 

def _has_insufficient_marker (text :str )->bool :
    normalized =_normalize_text (text )
    return any (marker in normalized for marker in _INSUFFICIENT_MARKERS )

def _normalize_text (text :str )->str :
    return re .sub (r"[^a-z0-9\u4e00-\u9fff]+"," ",text .lower ()).strip ()

def _tokenize_text (text :str )->list [str ]:
    normalized =_normalize_text (text )
    tokens =normalized .split ()
    cjk_sequences =re .findall (r"[\u4e00-\u9fff]{2,}",normalized )
    for sequence in cjk_sequences :
        if len (sequence )==2 :
            tokens .append (sequence )
            continue 
        for index in range (len (sequence )-1 ):
            tokens .append (sequence [index :index +2 ])
    return tokens 

def _signal_tokens (text :str )->list [str ]:
    return [token for token in _tokenize_text (text )if token not in _LOW_SIGNAL_TOKENS ]

def _contains_any (text :str ,markers :set [str ])->bool :
    return any (marker in text for marker in markers )

def _dedupe_preserve_order (items :list [str ])->list [str ]:
    seen :set [str ]=set ()
    result :list [str ]=[]
    for item in items :
        if item in seen :
            continue 
        seen .add (item )
        result .append (item )
    return result 

def _stable_id (prefix :str ,*parts :str )->str :
    material ="|".join (parts )
    digest =sha1 (material .encode ("utf-8")).hexdigest ()[:10 ]
    return f"{prefix}_{digest}"

def _system_label (system :str )->str :
    return _SYSTEM_LABELS .get (system ,system )

def _dimension_label (dimension :str )->str :
    return _DIMENSION_LABELS .get (dimension ,dimension )
