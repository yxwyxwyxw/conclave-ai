from __future__ import annotations 

from dataclasses import dataclass 
import threading 
from typing import Any ,Optional 

from divination_fusion .adapters import AdapterError ,AdapterRegistry ,ModelRequest 
from divination_fusion .agents import build_analysis_request 
from divination_fusion .battle import normalize_max_battle_rounds 
from divination_fusion .judge import apply_judgement_reviews ,review_judgements 
from divination_fusion .chart_engine import resolve_chart_data 
from divination_fusion .models import (
AnalysisRequest ,
Judgement ,
Rebuttal ,
RoleRuntimeConfig ,
SystemEvidence ,
WorkflowState ,
to_dict ,
)
from divination_fusion .prompts import analyzer_system_prompt ,analyzer_user_prompt_with_chart ,battler_system_prompt ,judge_system_prompt 
from divination_fusion .report import synthesize_report 
from divination_fusion .safety import apply_safety_policy 
from divination_fusion .services import normalize_profile 
from divination_fusion .session_store import SessionStore 
from divination_fusion .text_debate import (
analyzer_user_prompt ,
battler_user_prompt ,
extract_summary ,
judge_final_user_prompt ,
judge_issue_user_prompt ,
judge_round_user_prompt ,
local_issue_fallback ,
local_judgement_fallback ,
parse_final_judgement ,
parse_issue_text ,
parse_round_control ,
)

@dataclass 
class SessionRunInput :
    query :str 
    name :Optional [str ]
    birth_date :Optional [str ]
    birth_time :Optional [str ]
    birth_place :Optional [str ]
    timezone :Optional [str ]
    max_battle_rounds :int 
    credential_mode :str 
    provider_configs :dict [str ,dict [str ,str ]]
    api_keys :dict [str ,str ]

class BattleOrchestrator :
    def __init__ (self ,store :SessionStore ,adapters :AdapterRegistry )->None :
        self .store =store 
        self .adapters =adapters 

    def run (
    self ,
    session_id :str ,
    request_input :SessionRunInput ,
    *,
    cancel_event :Optional [threading .Event ]=None ,
    )->dict [str ,Any ]:
        analysis_request =build_analysis_request (
        request_input .query ,
        name =request_input .name ,
        birth_date =request_input .birth_date ,
        birth_time =request_input .birth_time ,
        birth_place =request_input .birth_place ,
        timezone =request_input .timezone ,
        metadata ={"max_battle_rounds":request_input .max_battle_rounds },
        )
        state =WorkflowState (request =analysis_request )
        try :
            self .store .update_snapshot (session_id =session_id ,status ="running",snapshot ={"phase":"starting"})
            self .store .append_event (
            session_id =session_id ,
            event_type ="session_started",
            payload ={"query":analysis_request .query ,"max_battle_rounds":request_input .max_battle_rounds },
            )

            normalized_profile =normalize_profile (analysis_request )
            state .normalized_profile =normalized_profile 
            self ._save_state (session_id ,state ,status ="running")
            self .store .append_event (
            session_id =session_id ,
            event_type ="profile_normalized",
            payload =to_dict (normalized_profile ),
            )

            evidence_list :list [SystemEvidence ]=[]
            bazi_chart_ctx ,ziwei_chart_ctx =resolve_chart_data (analysis_request ,normalized_profile )
            self .store .append_event (
            session_id =session_id ,
            event_type ="chart_resolved",
            payload ={"bazi_ok":bool (bazi_chart_ctx ),"ziwei_ok":bool (ziwei_chart_ctx )},
            )
            chart_contexts ={"bazi":bazi_chart_ctx ,"ziwei":ziwei_chart_ctx }
            for system_name in ("bazi","ziwei"):
                self ._ensure_not_cancelled (cancel_event )
                runtime =self ._role_runtime (request_input .provider_configs ,f"{system_name}_analyzer",system_name )
                try :
                    evidence =self ._run_analyzer (
                    runtime ,analysis_request ,normalized_profile ,request_input .api_keys ,
                    chart_context =chart_contexts .get (system_name ,""),
                    )
                    event_type ="analyzer_completed"
                except AdapterError as exc :
                    evidence =SystemEvidence (
                    system =system_name ,
                    summary =f"{system_name} 分析器调用失败，暂未产出分析文本。",
                    claims =[],
                    data_quality =0.0 ,
                    analysis_text ="",
                    warnings =[str (exc )],
                    )
                    event_type ="analyzer_failed"
                evidence_list .append (evidence )
                self .store .append_event (
                session_id =session_id ,
                event_type =event_type ,
                payload ={"system":system_name ,"evidence":to_dict (evidence )},
                )

            state .system_evidence =evidence_list 
            state .mapped_dimensions =[]
            state .debate_issues =self ._detect_issues_with_judge (
            analysis_request ,
            evidence_list ,
            request_input .provider_configs ,
            request_input .api_keys ,
            )
            self ._save_state (session_id ,state ,status ="running")
            self .store .append_event (
            session_id =session_id ,
            event_type ="issues_detected",
            payload ={"issues":to_dict (state .debate_issues ),"mapped_dimensions":[]},
            )

            max_rounds =normalize_max_battle_rounds (request_input .max_battle_rounds )
            for issue in state .debate_issues :
                self ._ensure_not_cancelled (cancel_event )
                if not self ._has_multi_party_analysis (issue ,evidence_list ):
                    issue .termination_reason ="single-sided-issue"
                    issue .summary ="当前只有单侧流派分析文本，未进入正式争论。"
                    self .store .append_event (
                    session_id =session_id ,
                    event_type ="issue_skipped",
                    issue_id =issue .issue_id ,
                    payload ={"reason":issue .termination_reason ,"issue":to_dict (issue ),"summary":issue .summary },
                    )
                    continue 

                issue .status ="debating"
                current_question =issue .question 
                issue_rebuttals :list [Rebuttal ]=[]
                for round_index in range (1 ,max_rounds +1 ):
                    self ._ensure_not_cancelled (cancel_event )
                    state .cross_exam .append (
                    self ._build_question (issue ,round_index ,current_question )
                    )
                    round_rebuttals :list [Rebuttal ]=[]
                    for system_name in ("bazi","ziwei"):
                        self .store .append_event (
                        session_id =session_id ,
                        event_type ="round_started",
                        issue_id =issue .issue_id ,
                        round_index =round_index ,
                        payload ={
                        "issue_id":issue .issue_id ,
                        "round_index":round_index ,
                        "target_system":system_name ,
                        "prompt":current_question ,
                        "scope_note":issue .scope_note ,
                        },
                        )
                        runtime =self ._role_runtime (
                        request_input .provider_configs ,
                        f"{system_name}_battler",
                        system_name ,
                        )
                        try :
                            rebuttal =self ._run_battler (
                            runtime ,
                            analysis_request ,
                            issue =issue ,
                            question =current_question ,
                            system_name =system_name ,
                            evidence_list =evidence_list ,
                            prior_rebuttals =issue_rebuttals ,
                            api_keys =request_input .api_keys ,
                            )
                        except AdapterError as exc :
                            issue .termination_reason ="model-round-failed"
                            issue .summary =str (exc )
                            self .store .append_event (
                            session_id =session_id ,
                            event_type ="round_failed",
                            issue_id =issue .issue_id ,
                            round_index =round_index ,
                            payload ={"error":str (exc ),"target_system":system_name },
                            )
                            round_rebuttals =[]
                            break 
                        rebuttal .round_index =round_index 
                        round_rebuttals .append (rebuttal )
                        issue_rebuttals .append (rebuttal )
                        state .debate_transcript .append (rebuttal )
                        self .store .append_event (
                        session_id =session_id ,
                        event_type ="round_completed",
                        issue_id =issue .issue_id ,
                        round_index =round_index ,
                        payload =to_dict (rebuttal ),
                        )

                    issue .rounds_completed =round_index 
                    if issue .termination_reason =="model-round-failed":
                        issue .status ="open"
                        break 
                    control =self ._run_judge_round_control (
                    request_input .provider_configs ,
                    request_input .api_keys ,
                    analysis_request ,
                    issue ,
                    issue_rebuttals [:-2 ],
                    round_rebuttals ,
                    )
                    if control ["moderation"]:
                        self .store .append_event (
                        session_id =session_id ,
                        event_type ="judge_moderated",
                        issue_id =issue .issue_id ,
                        round_index =round_index ,
                        payload =control ,
                        )
                    if control ["status"]=="结束":
                        issue .termination_reason =control ["termination_reason"]or "judge-stopped"
                        issue .summary =control ["moderation"]or "裁判认为当前争论已经足够，停止继续扩写。"
                        issue .status ="resolved"
                        break 
                    current_question =control ["next_question"]or current_question 

                if issue .termination_reason is None :
                    issue .termination_reason ="max-rounds-reached"
                    issue .summary =f"该争点已达到 {max_rounds} 轮上限，转入裁判终局。"
                    issue .status ="open"
                self ._save_state (session_id ,state ,status ="running")

            final_judgements :list [Judgement ]=[]
            for issue in state .debate_issues :
                self ._ensure_not_cancelled (cancel_event )
                rebuttals =[item for item in state .debate_transcript if item .issue_id ==issue .issue_id ]
                try :
                    judgement =self ._run_judge_final (
                    request_input .provider_configs ,
                    request_input .api_keys ,
                    analysis_request ,
                    issue ,
                    evidence_list ,
                    rebuttals ,
                    )
                except AdapterError :
                    disposition ,favored_system ,rationale ,conditions ,summary =local_judgement_fallback (issue ,rebuttals )
                    judgement =Judgement (
                    issue_id =issue .issue_id ,
                    disposition =disposition ,
                    favored_system =favored_system ,
                    rationale =rationale ,
                    conditions =conditions ,
                    cited_claim_ids =[],
                    summary =summary ,
                    )
                final_judgements .append (judgement )
                self .store .append_event (
                session_id =session_id ,
                event_type ="judge_completed",
                issue_id =issue .issue_id ,
                payload =to_dict (judgement ),
                )

            judgement_reviews =review_judgements (final_judgements ,state .debate_issues ,evidence_list )
            final_judgements =apply_judgement_reviews (final_judgements ,judgement_reviews )
            for review in judgement_reviews :
                self .store .append_event (
                session_id =session_id ,
                event_type ="judge_reviewed",
                issue_id =review .issue_id ,
                payload ={
                "issue_id":review .issue_id ,
                "passed":review .passed ,
                "extra_conditions":review .extra_conditions ,
                "invalid_cited_claim_ids":review .invalid_cited_claim_ids ,
                "missing_reservations":review .missing_reservations ,
                "verifier_status":"passed"if review .passed else "flagged",
                "verifier_summary":review .rationale_appendix ,
                },
                )
            state .judgement_reviews =[
            {
            "issue_id":review .issue_id ,
            "passed":review .passed ,
            "extra_conditions":review .extra_conditions ,
            "rationale_appendix":review .rationale_appendix ,
            "invalid_cited_claim_ids":review .invalid_cited_claim_ids ,
            "missing_reservations":review .missing_reservations ,
            }
            for review in judgement_reviews 
            ]
            state .judgements =final_judgements 

            report =apply_safety_policy (
            synthesize_report (
            analysis_request ,
            normalized_profile ,
            evidence_list ,
            final_judgements ,
            state .debate_issues ,
            )
            )
            state .fusion_report =report 
            final_state =to_dict (state )
            self .store .update_snapshot (
            session_id =session_id ,
            status ="completed",
            snapshot =final_state ,
            report =to_dict (report ),
            )
            self .store .append_event (
            session_id =session_id ,
            event_type ="report_ready",
            payload ={"fusion_report":to_dict (report )},
            )
            self .store .append_event (
            session_id =session_id ,
            event_type ="session_finished",
            payload ={"status":"completed"},
            )
            return final_state 
        except CancelledError :
            self .store .update_snapshot (session_id =session_id ,status ="cancelled",snapshot =to_dict (state ))
            self .store .append_event (
            session_id =session_id ,
            event_type ="session_cancelled",
            payload ={"status":"cancelled"},
            )
            return to_dict (state )
        except Exception as exc :
            self .store .update_snapshot (
            session_id =session_id ,
            status ="failed",
            snapshot =to_dict (state ),
            )
            self .store .append_event (
            session_id =session_id ,
            event_type ="session_failed",
            payload ={"error":str (exc )},
            )
            raise 

    def _run_analyzer (
    self ,
    runtime :RoleRuntimeConfig ,
    request :AnalysisRequest ,
    normalized_profile :Any ,
    api_keys :dict [str ,str ],
    chart_context :str ="",
    )->SystemEvidence :
        adapter =self .adapters .get (runtime .provider )
        user_prompt =(
        analyzer_user_prompt_with_chart (request .query ,request .focus_areas ,runtime .system_name ,chart_context )
        if chart_context 
        else analyzer_user_prompt (request .query ,request .focus_areas ,to_dict (normalized_profile ))
        )
        model_request =ModelRequest (
        provider =runtime .provider ,
        model =runtime .model ,
        role ="analyzer",
        system_name =runtime .system_name ,
        system_prompt =analyzer_system_prompt (runtime .system_name ),
        user_prompt =user_prompt ,
        schema_name ="plain_text",
        runtime_constraints ={"focus_areas":request .focus_areas },
        api_key =self ._resolve_api_key (runtime .provider ,api_keys ),
        )
        response =adapter .generate (model_request )
        analysis_text =response .payload ["text"]
        return SystemEvidence (
        system =runtime .system_name ,
        summary =extract_summary (analysis_text ),
        claims =[],
        data_quality =_analysis_data_quality (normalized_profile ),
        analysis_text =analysis_text ,
        warnings =[],
        )

    def _detect_issues_with_judge (
    self ,
    request :AnalysisRequest ,
    evidence_list :list [SystemEvidence ],
    provider_configs :dict [str ,dict [str ,str ]],
    api_keys :dict [str ,str ],
    )->list [Any ]:
        runtime =self ._role_runtime (provider_configs ,"judge","judge")
        adapter =self .adapters .get (runtime .provider )
        try :
            response =adapter .generate (
            ModelRequest (
            provider =runtime .provider ,
            model =runtime .model ,
            role ="judge",
            system_name ="judge",
            system_prompt =judge_system_prompt (),
            user_prompt =judge_issue_user_prompt (request .query ,evidence_list ),
            schema_name ="plain_text",
            runtime_constraints ={"phase":"issue-detection"},
            api_key =self ._resolve_api_key (runtime .provider ,api_keys ),
            )
            )
            issues =parse_issue_text (response .payload ["text"],request .focus_areas )
            return issues or local_issue_fallback (evidence_list ,request .focus_areas )
        except AdapterError :
            return local_issue_fallback (evidence_list ,request .focus_areas )

    def _run_battler (
    self ,
    runtime :RoleRuntimeConfig ,
    request :AnalysisRequest ,
    *,
    issue :Any ,
    question :str ,
    system_name :str ,
    evidence_list :list [SystemEvidence ],
    prior_rebuttals :list [Rebuttal ],
    api_keys :dict [str ,str ],
    )->Rebuttal :
        own_analysis =next ((item .analysis_text for item in evidence_list if item .system ==system_name ),"")
        opponent_system ="ziwei"if system_name =="bazi"else "bazi"
        opponent_analysis =next ((item .analysis_text for item in evidence_list if item .system ==opponent_system ),"")
        adapter =self .adapters .get (runtime .provider )
        model_request =ModelRequest (
        provider =runtime .provider ,
        model =runtime .model ,
        role ="battler",
        system_name =runtime .system_name ,
        system_prompt =battler_system_prompt (runtime .system_name ),
        user_prompt =battler_user_prompt (
        query =request .query ,
        issue =issue ,
        system_name =system_name ,
        own_analysis =own_analysis ,
        opponent_analysis =opponent_analysis ,
        prior_rebuttals =prior_rebuttals ,
        judge_question =question ,
        ),
        schema_name ="plain_text",
        runtime_constraints ={"issue_id":issue .issue_id },
        api_key =self ._resolve_api_key (runtime .provider ,api_keys ),
        )
        response =adapter .generate (model_request )
        text =response .payload ["text"]
        return Rebuttal (
        issue_id =issue .issue_id ,
        round_index =0 ,
        system =runtime .system_name ,
        response =text ,
        public_response =text ,
        stance ="respond",
        summary_hint =extract_summary (text ),
        )

    def _run_judge_round_control (
    self ,
    provider_configs :dict [str ,dict [str ,str ]],
    api_keys :dict [str ,str ],
    request :AnalysisRequest ,
    issue :Any ,
    prior_rebuttals :list [Rebuttal ],
    current_round :list [Rebuttal ],
    )->dict [str ,str ]:
        runtime =self ._role_runtime (provider_configs ,"judge","judge")
        adapter =self .adapters .get (runtime .provider )
        response =adapter .generate (
        ModelRequest (
        provider =runtime .provider ,
        model =runtime .model ,
        role ="judge",
        system_name ="judge",
        system_prompt =judge_system_prompt (),
        user_prompt =judge_round_user_prompt (
        query =request .query ,
        issue =issue ,
        prior_rebuttals =prior_rebuttals ,
        current_round =current_round ,
        ),
        schema_name ="plain_text",
        runtime_constraints ={"phase":"moderation","issue_id":issue .issue_id },
        api_key =self ._resolve_api_key (runtime .provider ,api_keys ),
        )
        )
        return parse_round_control (response .payload ["text"])

    def _run_judge_final (
    self ,
    provider_configs :dict [str ,dict [str ,str ]],
    api_keys :dict [str ,str ],
    request :AnalysisRequest ,
    issue :Any ,
    evidence_list :list [SystemEvidence ],
    rebuttals :list [Rebuttal ],
    )->Judgement :
        runtime =self ._role_runtime (provider_configs ,"judge","judge")
        adapter =self .adapters .get (runtime .provider )
        response =adapter .generate (
        ModelRequest (
        provider =runtime .provider ,
        model =runtime .model ,
        role ="judge",
        system_name ="judge",
        system_prompt =judge_system_prompt (),
        user_prompt =judge_final_user_prompt (
        query =request .query ,
        issue =issue ,
        evidence_list =evidence_list ,
        rebuttals =rebuttals ,
        ),
        schema_name ="plain_text",
        runtime_constraints ={"phase":"final","issue_id":issue .issue_id },
        api_key =self ._resolve_api_key (runtime .provider ,api_keys ),
        )
        )
        parsed =parse_final_judgement (response .payload ["text"])
        return Judgement (
        issue_id =issue .issue_id ,
        disposition =parsed ["disposition"],
        favored_system =parsed ["favored_system"],
        rationale =parsed ["rationale"]or response .payload ["text"],
        conditions =parsed ["conditions"],
        cited_claim_ids =[],
        summary =parsed ["summary"]or parsed ["rationale"],
        )

    def _resolve_api_key (self ,provider :str ,api_keys :dict [str ,str ])->Optional [str ]:
        return api_keys .get (provider )

    def _role_runtime (
    self ,
    provider_configs :dict [str ,dict [str ,str ]],
    role_key :str ,
    system_name :str ,
    )->RoleRuntimeConfig :
        payload =provider_configs [role_key ]
        return RoleRuntimeConfig (
        role =role_key ,
        system_name =system_name ,
        provider =payload ["provider"],
        model =payload ["model"],
        )

    def _save_state (self ,session_id :str ,state :WorkflowState ,*,status :str )->None :
        self .store .update_snapshot (session_id =session_id ,status =status ,snapshot =to_dict (state ))

    def _has_multi_party_analysis (self ,issue :Any ,evidence_list :list [SystemEvidence ])->bool :
        systems ={item .system for item in evidence_list if item .analysis_text }
        needed ={name for name ,view in issue .system_views .items ()if view }
        return len (systems &needed )>=2 if needed else len (systems )>=2 

    def _build_question (self ,issue :Any ,round_index :int ,prompt :str )->Any :
        from divination_fusion .models import CrossExamQuestion 

        return CrossExamQuestion (
        issue_id =issue .issue_id ,
        round_index =round_index ,
        target_system ="both",
        prompt =prompt ,
        rationale =issue .scope_note or "",
        )

    def _ensure_not_cancelled (self ,cancel_event :Optional [threading .Event ])->None :
        if cancel_event is not None and cancel_event .is_set ():
            raise CancelledError ()

class CancelledError (RuntimeError ):
    pass 

def _analysis_data_quality (normalized_profile :Any )->float :
    completeness =getattr (normalized_profile ,"completeness",None )
    if getattr (completeness ,"value","")=="exact":
        return 0.9 
    if getattr (completeness ,"value","")=="estimated":
        return 0.75 
    if getattr (completeness ,"value","")=="date-only":
        return 0.6 
    return 0.45 
