from __future__ import annotations 

from dataclasses import dataclass ,field ,fields ,is_dataclass 
from datetime import datetime 
from enum import Enum 
from typing import Any ,Optional 

class DataCompleteness (str ,Enum ):
    EXACT ="exact"
    ESTIMATED ="estimated"
    DATE_ONLY ="date-only"
    UNKNOWN ="unknown"

class ClaimRelation (str ,Enum ):
    CONSENSUS ="consensus"
    TENSION ="tension"
    CONTRADICTION ="contradiction"
    INSUFFICIENT_DATA ="insufficient-data"

class JudgementDisposition (str ,Enum ):
    FAVOR_A ="favor-a"
    FAVOR_B ="favor-b"
    CONDITIONAL ="conditional"
    UNRESOLVED ="unresolved"
    MUTUAL_VALIDITY ="mutual-validity"

@dataclass 
class PersonProfile :
    name :Optional [str ]=None 
    birth_date :Optional [str ]=None 
    birth_time :Optional [str ]=None 
    birth_place :Optional [str ]=None 
    timezone :Optional [str ]=None 
    calendar :str ="gregorian"
    gender :Optional [str ]=None 

@dataclass 
class AnalysisRequest :
    query :str 
    profile :PersonProfile 
    focus_areas :list [str ]
    output_style :str ="concise"
    language :str ="zh-CN"
    metadata :dict [str ,Any ]=field (default_factory =dict )

@dataclass 
class NormalizedProfile :
    name :Optional [str ]
    timezone :str 
    calendar :str 
    birth_place :Optional [str ]
    birth_datetime_local :Optional [str ]
    birth_datetime_utc :Optional [str ]
    completeness :DataCompleteness 
    missing_fields :list [str ]
    notes :list [str ]

@dataclass 
class Claim :
    claim_id :str 
    system :str 
    dimension :str 
    statement :str 
    evidence :list [str ]
    depends_on :list [str ]=field (default_factory =list )
    qualifiers :list [str ]=field (default_factory =list )
    claim_type :str ="interpretation"
    basis_type :str ="heuristic"
    basis_value :Optional [str ]=None 
    uncertainty_reasons :list [str ]=field (default_factory =list )
    required_inputs :list [str ]=field (default_factory =list )
    scope :str ="issue"

@dataclass 
class SystemEvidence :
    system :str 
    summary :str 
    claims :list [Claim ]
    data_quality :float 
    analysis_text :str =""
    warnings :list [str ]=field (default_factory =list )

@dataclass 
class MappedDimension :
    dimension :str 
    system_claim_ids :dict [str ,list [str ]]
    notes :list [str ]=field (default_factory =list )

@dataclass 
class DebateIssue :
    issue_id :str 
    dimension :str 
    relation :ClaimRelation 
    claim_ids :list [str ]
    question :str 
    severity :float 
    title :Optional [str ]=None 
    system_views :dict [str ,str ]=field (default_factory =dict )
    scope_note :Optional [str ]=None 
    status :str ="open"
    rounds_completed :int =0 
    termination_reason :Optional [str ]=None 
    summary :Optional [str ]=None 
    stability_status :Optional [str ]=None 
    stability_summary :Optional [str ]=None 

@dataclass 
class CrossExamQuestion :
    issue_id :str 
    round_index :int 
    target_system :str 
    prompt :str 
    rationale :str 

@dataclass 
class Rebuttal :
    issue_id :str 
    round_index :int 
    system :str 
    response :str 
    supported_claim_ids :list [str ]=field (default_factory =list )
    public_response :str =""
    stance :str ="maintain"
    conceded_points :list [str ]=field (default_factory =list )
    still_disputed_points :list [str ]=field (default_factory =list )
    argument_points :list [str ]=field (default_factory =list )
    new_argument_points :list [str ]=field (default_factory =list )
    summary_hint :Optional [str ]=None 
    stop_signal :bool =False 
    judge_feedback :Optional [str ]=None 

    def __post_init__ (self )->None :
        if not self .public_response :
            self .public_response =self .response 
        if isinstance (self .summary_hint ,str ):
            self .summary_hint =self .summary_hint .strip ()or None 
        if not self .summary_hint :
            self .summary_hint =self .public_response 

@dataclass 
class Judgement :
    issue_id :str 
    disposition :JudgementDisposition 
    favored_system :Optional [str ]
    rationale :str 
    conditions :list [str ]=field (default_factory =list )
    cited_claim_ids :list [str ]=field (default_factory =list )
    summary :Optional [str ]=None 
    verifier_status :Optional [str ]=None 
    verifier_summary :Optional [str ]=None 

@dataclass 
class FusionReport :
    summary :str 
    consensus_points :list [str ]
    disagreement_points :list [str ]
    reservations :list [str ]
    suggested_followups :list [str ]
    raw_sections :dict [str ,Any ]=field (default_factory =dict )

@dataclass 
class TraceStep :
    step :str 
    timestamp :str 
    input_ref :str 
    output_ref :str 
    prompt_version :str 
    model_version :str 
    rule_version :str 
    metadata :dict [str ,Any ]=field (default_factory =dict )

@dataclass 
class TraceMetadata :
    run_id :str 
    created_at :str 
    input_version :str 
    prompt_versions :dict [str ,str ]
    rule_versions :dict [str ,str ]
    model_versions :dict [str ,str ]
    steps :list [TraceStep ]=field (default_factory =list )

@dataclass 
class WorkflowState :
    request :AnalysisRequest 
    normalized_profile :Optional [NormalizedProfile ]=None 
    system_evidence :list [SystemEvidence ]=field (default_factory =list )
    mapped_dimensions :list [MappedDimension ]=field (default_factory =list )
    debate_issues :list [DebateIssue ]=field (default_factory =list )
    cross_exam :list [CrossExamQuestion ]=field (default_factory =list )
    debate_transcript :list [Rebuttal ]=field (default_factory =list )
    judgements :list [Judgement ]=field (default_factory =list )
    judgement_reviews :list [dict [str ,Any ]]=field (default_factory =list )
    fusion_report :Optional [FusionReport ]=None 
    trace_metadata :Optional [TraceMetadata ]=None 

@dataclass 
class ProviderConfig :
    provider :str 
    mode :str 
    api_key_present :bool 

@dataclass 
class RoleRuntimeConfig :
    role :str 
    system_name :str 
    provider :str 
    model :str 

@dataclass 
class RoundRecord :
    issue_id :str 
    round_index :int 
    target_system :str 
    status :str 
    question :Optional [CrossExamQuestion ]=None 
    rebuttal :Optional [Rebuttal ]=None 

@dataclass 
class BattleEvent :
    seq :int 
    session_id :str 
    event_type :str 
    created_at :str 
    payload :dict [str ,Any ]=field (default_factory =dict )
    issue_id :Optional [str ]=None 
    round_index :Optional [int ]=None 

@dataclass 
class SessionRecord :
    session_id :str 
    status :str 
    created_at :str 
    updated_at :str 
    request_payload :dict [str ,Any ]
    snapshot :dict [str ,Any ]=field (default_factory =dict )
    report :Optional [dict [str ,Any ]]=None 
    auth_mode :str ="server"
    run_dir :Optional [str ]=None 

def now_iso ()->str :
    return datetime .utcnow ().replace (microsecond =0 ).isoformat ()+"Z"

def to_dict (value :Any )->Any :
    if is_dataclass (value ):
        return {field .name :to_dict (getattr (value ,field .name ))for field in fields (value )}
    if isinstance (value ,Enum ):
        return value .value 
    if isinstance (value ,list ):
        return [to_dict (item )for item in value ]
    if isinstance (value ,dict ):
        return {key :to_dict (item )for key ,item in value .items ()}
    return value 
