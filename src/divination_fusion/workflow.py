from __future__ import annotations

from pathlib import Path
from typing import Union

from divination_fusion.battle import (
    detect_debate_issues,
    map_dimensions,
    normalize_max_battle_rounds,
    run_battle,
)
from divination_fusion.judge import apply_judgement_reviews, judge_issues, review_judgements
from divination_fusion.models import AnalysisRequest, WorkflowState, to_dict
from divination_fusion.report import synthesize_report
from divination_fusion.safety import apply_safety_policy
from divination_fusion.services import normalize_profile
from divination_fusion.systems.astrology import analyze_astrology
from divination_fusion.systems.bazi import analyze_bazi
from divination_fusion.trace import TraceRecorder, load_trace_metadata


def run_analysis(
    request: AnalysisRequest,
    *,
    trace_root: Union[str, Path] = "runs",
    battle_max_rounds: int | None = None,
) -> WorkflowState:
    trace = TraceRecorder.create(Path(trace_root))
    state = WorkflowState(request=request, trace_metadata=trace.metadata)

    normalized = normalize_profile(request)
    state.normalized_profile = normalized
    trace.record(
        "normalize_profile",
        request,
        normalized,
        prompt_version="deterministic-v1",
        model_version="code",
        rule_version="profile-rules-v1",
    )

    bazi = analyze_bazi(request, normalized)
    astrology = analyze_astrology(request, normalized)
    state.system_evidence = [bazi, astrology]
    trace.record(
        "analyzers",
        {"request": request, "profile": normalized},
        state.system_evidence,
        prompt_version="heuristic-v1",
        model_version="code",
        rule_version="system-rules-v1",
    )

    mapped_dimensions = map_dimensions(state.system_evidence)
    debate_issues = detect_debate_issues(state.system_evidence, mapped_dimensions)
    configured_max_rounds = battle_max_rounds
    if configured_max_rounds is not None:
        configured_max_rounds = normalize_max_battle_rounds(configured_max_rounds)
    else:
        configured_max_rounds = normalize_max_battle_rounds(
            request.metadata.get("max_battle_rounds")
            if isinstance(request.metadata, dict)
            else None
        )
    cross_exam, rebuttals = run_battle(
        debate_issues,
        state.system_evidence,
        max_rounds=configured_max_rounds,
    )
    state.mapped_dimensions = mapped_dimensions
    state.debate_issues = debate_issues
    state.cross_exam = cross_exam
    state.debate_transcript = rebuttals
    trace.record(
        "battle",
        state.system_evidence,
        {
            "mapped_dimensions": mapped_dimensions,
            "issues": debate_issues,
            "cross_exam": cross_exam,
            "rebuttals": rebuttals,
        },
        prompt_version="battle-v1",
        model_version="code",
        rule_version="battle-rules-v1",
        metadata={"max_rounds": configured_max_rounds},
    )

    judgements = judge_issues(debate_issues, state.system_evidence, rebuttals)
    judgement_reviews = review_judgements(judgements, debate_issues, state.system_evidence)
    judgements = apply_judgement_reviews(judgements, judgement_reviews)
    state.judgements = judgements
    state.judgement_reviews = [
        {
            "issue_id": review.issue_id,
            "passed": review.passed,
            "extra_conditions": review.extra_conditions,
            "rationale_appendix": review.rationale_appendix,
            "invalid_cited_claim_ids": review.invalid_cited_claim_ids,
            "missing_reservations": review.missing_reservations,
        }
        for review in judgement_reviews
    ]
    trace.record(
        "judge",
        {
            "issues": debate_issues,
            "evidence": state.system_evidence,
            "rebuttals": rebuttals,
            "reviews": judgement_reviews,
        },
        judgements,
        prompt_version="judge-v1",
        model_version="code",
        rule_version="judge-rules-v1",
    )

    fusion_report = synthesize_report(
        request,
        normalized,
        state.system_evidence,
        judgements,
        debate_issues,
    )
    state.fusion_report = apply_safety_policy(fusion_report)
    trace.record(
        "report",
        {
            "request": request,
            "profile": normalized,
            "issues": debate_issues,
            "judgements": judgements,
        },
        state.fusion_report,
        prompt_version="report-v1",
        model_version="code",
        rule_version="report-rules-v1",
        metadata={"summary_length": len(state.fusion_report.summary)},
    )
    state.trace_metadata = trace.metadata
    return state


def replay_trace(trace_dir: Union[str, Path]) -> dict[str, object]:
    root = Path(trace_dir)
    metadata = load_trace_metadata(root)
    metadata_text = (root / "trace_metadata.json").read_text(encoding="utf-8")
    metadata_parsed = to_dict(metadata)
    return {
        "trace_dir": str(root),
        "run_id": metadata.run_id,
        "created_at": metadata.created_at,
        "step_count": len(metadata.steps),
        "step_names": [step.step for step in metadata.steps],
        "metadata": metadata_parsed,
        "metadata_text": metadata_text,
    }


def state_to_dict(state: WorkflowState) -> dict[str, object]:
    return to_dict(state)
