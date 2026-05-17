from divination_fusion.agents import build_analysis_request
from divination_fusion.models import (
    ClaimRelation,
    DataCompleteness,
    DebateIssue,
    Judgement,
    JudgementDisposition,
    NormalizedProfile,
)
from divination_fusion.report import synthesize_report


def test_synthesize_report_keeps_missing_data_visible():
    request = build_analysis_request(
        "请综合分析我的事业和感情趋势",
        birth_date="1990-06-12",
        timezone="Asia/Shanghai",
    )
    profile = NormalizedProfile(
        name="Smoke Test",
        timezone="Asia/Shanghai",
        calendar="gregorian",
        birth_place=None,
        birth_datetime_local="1990-06-12",
        birth_datetime_utc=None,
        completeness=DataCompleteness.DATE_ONLY,
        missing_fields=["birth_time", "birth_place"],
        notes=["birth_time_missing_used_date_only_normalization"],
    )
    issues = [
        DebateIssue(
            issue_id="issue-1",
            dimension="career",
            relation=ClaimRelation.INSUFFICIENT_DATA,
            claim_ids=["claim-1"],
            question="career 维度的资料仍不足，是否存在缺失字段或过低置信度导致无法裁决？",
            severity=0.7,
            status="open",
        )
    ]
    judgements = [
        Judgement(
            issue_id="issue-1",
            disposition=JudgementDisposition.UNRESOLVED,
            favored_system=None,
            rationale="career 维度暂无法裁决，需要补充出生时辰。",
            conditions=["补充出生时辰"],
            cited_claim_ids=["claim-1"],
        )
    ]

    report = synthesize_report(request, profile, [], judgements, issues)

    assert "仍缺少出生时辰、出生地点" in report.summary
    assert report.raw_sections["结论摘要"] == report.summary
    assert report.raw_sections["保留意见"] == report.reservations
    assert report.raw_sections["建议补充资料"] == report.suggested_followups
    assert any("优先补充出生时辰、出生地点" in item for item in report.suggested_followups)
    assert any("结论应按保守口径理解" in item for item in report.reservations)
    assert any("继续追问事业维度" in item for item in report.suggested_followups)


def test_synthesize_report_keeps_conditional_judgements_out_of_consensus():
    request = build_analysis_request(
        "请综合分析我的事业和感情趋势",
        birth_date="1990-06-12",
        timezone="Asia/Shanghai",
    )
    profile = NormalizedProfile(
        name="Smoke Test",
        timezone="Asia/Shanghai",
        calendar="gregorian",
        birth_place="Shanghai",
        birth_datetime_local="1990-06-12T07:45:00",
        birth_datetime_utc="1990-06-12T23:45:00Z",
        completeness=DataCompleteness.EXACT,
        missing_fields=[],
        notes=[],
    )
    issues = [
        DebateIssue(
            issue_id="issue-1",
            dimension="career",
            relation=ClaimRelation.CONSENSUS,
            claim_ids=["claim-1"],
            question="career 维度是否形成一致判断？",
            severity=0.0,
            status="closed",
        ),
        DebateIssue(
            issue_id="issue-2",
            dimension="relationship",
            relation=ClaimRelation.TENSION,
            claim_ids=["claim-2"],
            question="relationship 维度的条件边界是什么？",
            severity=0.6,
            status="open",
        ),
    ]
    judgements = [
        Judgement(
            issue_id="issue-1",
            disposition=JudgementDisposition.MUTUAL_VALIDITY,
            favored_system=None,
            rationale="career 维度已形成一致判断。",
            conditions=[],
            cited_claim_ids=["claim-1"],
        ),
        Judgement(
            issue_id="issue-2",
            disposition=JudgementDisposition.CONDITIONAL,
            favored_system="astrology",
            rationale="relationship 维度当前更偏向 astrology，但仍只在条件边界内成立。",
            conditions=["需要补充适用前提"],
            cited_claim_ids=["claim-2"],
        ),
    ]

    report = synthesize_report(request, profile, [], judgements, issues)

    assert any("已形成一致判断" in item for item in report.consensus_points)
    assert all("条件边界" not in item for item in report.consensus_points)
    assert any("感情：" in item for item in report.disagreement_points)
    assert any("条件性结论" in item for item in report.reservations)
    assert any("条件边界" in item for item in report.suggested_followups)
    assert "条件性判断" in report.summary
