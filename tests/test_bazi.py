from divination_fusion.models import DataCompleteness, NormalizedProfile
from divination_fusion.systems.bazi import analyze_bazi
from divination_fusion.agents.intake import build_analysis_request


def _profile() -> NormalizedProfile:
    return NormalizedProfile(
        name="Demo User",
        timezone="Asia/Shanghai",
        calendar="gregorian",
        birth_place="Shanghai",
        birth_datetime_local="1990-06-12T07:45:00",
        birth_datetime_utc="1990-06-12T23:45:00Z",
        completeness=DataCompleteness.EXACT,
        missing_fields=[],
        notes=[],
    )


def test_analyze_bazi_returns_structured_evidence():
    request = build_analysis_request(
        "请综合分析我的事业和感情趋势",
        name="Demo User",
        birth_date="1990-06-12",
        birth_time="07:45",
        birth_place="Shanghai",
        timezone="Asia/Shanghai",
        focus_areas=["career", "relationship"],
    )

    evidence = analyze_bazi(request, _profile())

    assert evidence.system == "bazi"
    assert evidence.data_quality == 0.9
    assert [claim.dimension for claim in evidence.claims] == ["career", "relationship", "risk"]
    assert all(claim.claim_id.startswith("bazi-") for claim in evidence.claims)
    assert all(claim.system == "bazi" for claim in evidence.claims)
    assert evidence.summary == "八字侧为Demo User生成了3条结构化主张，画像完整度为完整。"
    assert evidence.claims[0].statement.startswith("事业发展更适合累积推进")
    assert evidence.claims[0].evidence[0] == "关注领域：事业、感情"
    assert evidence.claims[0].evidence[1] == "画像完整度：完整"
    assert evidence.claims[2].evidence[-1] == "风险依据：主要看画像完整度和缺失项"


def test_analyze_bazi_is_deterministic_for_same_inputs():
    request = build_analysis_request(
        "请综合分析我的事业和感情趋势",
        name="Demo User",
        birth_date="1990-06-12",
        birth_time="07:45",
        birth_place="Shanghai",
        timezone="Asia/Shanghai",
        focus_areas=["career", "relationship"],
    )

    first = analyze_bazi(request, _profile())
    second = analyze_bazi(request, _profile())

    assert [claim.claim_id for claim in first.claims] == [claim.claim_id for claim in second.claims]
    assert first.summary == second.summary
    assert first.warnings == second.warnings
    assert first.claims[1].statement == second.claims[1].statement


def test_analyze_bazi_warns_on_missing_time():
    request = build_analysis_request(
        "请看一下性格和事业",
        name="No Time User",
        birth_date="1990-06-12",
        birth_place="Shanghai",
        timezone="Asia/Shanghai",
        focus_areas=["personality", "career"],
    )
    profile = NormalizedProfile(
        name="No Time User",
        timezone="Asia/Shanghai",
        calendar="gregorian",
        birth_place="Shanghai",
        birth_datetime_local=None,
        birth_datetime_utc=None,
        completeness=DataCompleteness.DATE_ONLY,
        missing_fields=["birth_time"],
        notes=["birth_time missing"],
    )

    evidence = analyze_bazi(request, profile)

    assert any("时辰相关判断" in warning for warning in evidence.warnings)
    assert any("出生时间不可用" in warning for warning in evidence.warnings)
    assert any(claim.dimension == "risk" for claim in evidence.claims)
    assert "画像完整度为仅日期" in evidence.summary
