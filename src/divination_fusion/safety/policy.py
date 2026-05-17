from __future__ import annotations

from typing import Any

from divination_fusion.models import FusionReport


ABSOLUTE_PHRASES = (
    "一定会",
    "绝对",
    "注定",
    "百分之百",
)

RISKY_TERMS = {
    "医疗": "本报告不构成医疗建议，如涉及健康问题请咨询持证医生。",
    "法律": "本报告不构成法律建议，如涉及法律事项请咨询专业律师。",
    "投资": "本报告不构成投资建议，请结合风险承受能力独立判断。",
}


def apply_safety_policy(report: FusionReport) -> FusionReport:
    summary = _soften(report.summary)
    consensus = [_soften(item) for item in report.consensus_points]
    disagreement = [_soften(item) for item in report.disagreement_points]
    reservations = [_soften(item) for item in report.reservations]
    suggested_followups = [_soften(item) for item in report.suggested_followups]
    raw_sections = _soften_value(report.raw_sections)

    combined = " ".join(
        [
            summary,
            *consensus,
            *disagreement,
            *reservations,
            *suggested_followups,
            *_flatten_text(raw_sections),
        ]
    )
    for trigger, notice in RISKY_TERMS.items():
        if trigger in combined and notice not in reservations:
            reservations.append(notice)

    return FusionReport(
        summary=summary,
        consensus_points=consensus,
        disagreement_points=disagreement,
        reservations=reservations,
        suggested_followups=suggested_followups,
        raw_sections=raw_sections,
    )


def _soften(text: str) -> str:
    softened = text
    for phrase in ABSOLUTE_PHRASES:
        softened = softened.replace(phrase, "较可能")
    return softened


def _soften_value(value: Any) -> Any:
    if isinstance(value, str):
        return _soften(value)
    if isinstance(value, list):
        return [_soften_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _soften_value(item) for key, item in value.items()}
    return value


def _flatten_text(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        flattened: list[str] = []
        for item in value:
            flattened.extend(_flatten_text(item))
        return flattened
    if isinstance(value, dict):
        flattened: list[str] = []
        for item in value.values():
            flattened.extend(_flatten_text(item))
        return flattened
    return []
