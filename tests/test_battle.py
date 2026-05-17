from divination_fusion.battle import (
    build_cross_exam_questions,
    build_rebuttals,
    detect_debate_issues,
    map_dimensions,
    normalize_max_battle_rounds,
    run_battle,
)
from divination_fusion.models import Claim, ClaimRelation, SystemEvidence


def _make_evidence() -> list[SystemEvidence]:
    return [
        SystemEvidence(
            system="bazi",
            summary="八字侧更强调事业的稳定增长。",
            claims=[
                Claim(
                    claim_id="bazi_career_1",
                    system="bazi",
                    dimension="career",
                    statement="事业走势偏稳定，适合长期积累与持续增长。",
                    evidence=["year pillar", "day master"],
                ),
                Claim(
                    claim_id="bazi_relationship_1",
                    system="bazi",
                    dimension="relationship",
                    statement="感情层面较开放，但仍需要明确边界。",
                    evidence=["peach blossom"],
                ),
            ],
            data_quality=0.88,
        ),
        SystemEvidence(
            system="astrology",
            summary="星盘侧认为事业有机会，但存在波动。",
            claims=[
                Claim(
                    claim_id="astro_career_1",
                    system="astrology",
                    dimension="career",
                    statement="事业机会明显，但短期波动也较强。",
                    evidence=["10th house"],
                ),
                Claim(
                    claim_id="astro_relationship_1",
                    system="astrology",
                    dimension="relationship",
                    statement="感情关系较开放，适合先建立边界。",
                    evidence=["venus"],
                ),
            ],
            data_quality=0.9,
        ),
    ]


def test_map_dimensions_groups_claims_by_dimension():
    mapped = map_dimensions(_make_evidence())
    assert [item.dimension for item in mapped] == ["career", "relationship"]
    assert mapped[0].system_claim_ids["bazi"] == ["bazi_career_1"]
    assert mapped[0].system_claim_ids["astrology"] == ["astro_career_1"]


def test_detect_debate_issues_identifies_non_consensus_dimensions():
    mapped = map_dimensions(_make_evidence())
    issues = detect_debate_issues(_make_evidence(), mapped)
    assert len(issues) == 1
    assert issues[0].dimension == "career"
    assert issues[0].relation in {ClaimRelation.TENSION, ClaimRelation.CONTRADICTION}


def test_cross_exam_and_rebuttal_are_issue_scoped():
    evidence = _make_evidence()
    issues = detect_debate_issues(evidence, map_dimensions(evidence))
    questions = build_cross_exam_questions(issues, evidence)
    rebuttals = build_rebuttals(questions, issues, evidence)

    assert len(questions) == 1
    assert questions[0].issue_id == issues[0].issue_id
    assert questions[0].prompt.startswith("围绕 issue")
    assert "事业" in questions[0].prompt
    assert len(rebuttals) == 1
    assert rebuttals[0].issue_id == issues[0].issue_id
    assert rebuttals[0].supported_claim_ids
    assert rebuttals[0].supported_claim_ids == ["astro_career_1"]
    assert "感情关系较开放" not in rebuttals[0].response
    assert "仅就 issue" in rebuttals[0].response
    assert "不延伸到其他维度" in rebuttals[0].response


def test_run_battle_supports_multiple_rounds_and_round_cap():
    evidence = _make_evidence()
    issues = detect_debate_issues(evidence, map_dimensions(evidence))

    questions, rebuttals = run_battle(issues, evidence, max_rounds=4)

    assert [question.round_index for question in questions] == [1, 2, 3, 4]
    assert [question.target_system for question in questions] == ["astrology", "bazi", "astrology", "bazi"]
    assert [rebuttal.round_index for rebuttal in rebuttals] == [1, 2, 3, 4]
    assert all("第" in rebuttal.response for rebuttal in rebuttals)
    assert all(rebuttal.public_response for rebuttal in rebuttals)
    assert issues[0].rounds_completed == 4
    assert issues[0].termination_reason == "max-rounds-reached"
    assert issues[0].status == "open"


def test_run_battle_can_stop_early_when_recent_cycles_stall():
    evidence = _make_evidence()
    issues = detect_debate_issues(evidence, map_dimensions(evidence))

    questions, rebuttals = run_battle(issues, evidence, max_rounds=6)

    assert [question.round_index for question in questions] == [1, 2, 3, 4]
    assert [rebuttal.round_index for rebuttal in rebuttals] == [1, 2, 3, 4]
    assert issues[0].rounds_completed == 4
    assert issues[0].termination_reason == "stability-stop"


def test_normalize_max_battle_rounds_caps_at_hard_limit():
    assert normalize_max_battle_rounds(4) == 4
    assert normalize_max_battle_rounds(80) == 50


def test_detect_debate_issues_marks_insufficient_data():
    evidence = [
        SystemEvidence(
            system="bazi",
            summary="只有单条低置信度事业信息。",
            claims=[
                Claim(
                    claim_id="bazi_career_low",
                    system="bazi",
                    dimension="career",
                    statement="资料有限，事业倾向只能暂时保留。",
                    evidence=[],
                )
            ],
            data_quality=0.3,
            warnings=["missing birth time"],
        )
    ]
    mapped = map_dimensions(evidence)
    issues = detect_debate_issues(evidence, mapped)
    assert len(issues) == 1
    assert issues[0].relation == ClaimRelation.INSUFFICIENT_DATA


def test_detect_debate_issues_ignores_low_signal_chinese_overlap():
    evidence = [
        SystemEvidence(
            system="bazi",
            summary="八字侧事业判断。",
            claims=[
                Claim(
                    claim_id="bazi_career_cn",
                    system="bazi",
                    dimension="career",
                    statement="事业发展更适合累积推进，尤其在上午节奏里更容易看见结构感。",
                    evidence=[],
                )
            ],
            data_quality=0.9,
        ),
        SystemEvidence(
            system="astrology",
            summary="星盘侧事业判断。",
            claims=[
                Claim(
                    claim_id="astro_career_cn",
                    system="astrology",
                    dimension="career",
                    statement="出生于夏季，职业倾向更容易围绕表达能见度与主导性展开。",
                    evidence=[],
                )
            ],
            data_quality=0.9,
        ),
    ]

    issues = detect_debate_issues(evidence, map_dimensions(evidence))

    assert len(issues) == 1
    assert issues[0].dimension == "career"
    assert issues[0].relation == ClaimRelation.TENSION
