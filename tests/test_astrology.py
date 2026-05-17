from divination_fusion.models import AnalysisRequest, DataCompleteness, NormalizedProfile, PersonProfile
from divination_fusion.systems.astrology import analyze_astrology


def test_analyze_astrology_exports_structured_evidence():
    request = AnalysisRequest(
        query="请看事业和感情",
        profile=PersonProfile(name="Demo", birth_date="1990-06-12", birth_time="07:45", birth_place="Shanghai"),
        focus_areas=["career", "relationship"],
    )
    profile = NormalizedProfile(
        name="Demo",
        timezone="Asia/Shanghai",
        calendar="gregorian",
        birth_place="Shanghai",
        birth_datetime_local="1990-06-12T07:45:00",
        birth_datetime_utc="1990-06-12T23:45:00Z",
        completeness=DataCompleteness.EXACT,
        missing_fields=[],
        notes=["demo"],
    )

    evidence = analyze_astrology(request, profile)

    assert evidence.system == "astrology"
    assert evidence.claims[0].claim_id == "astrology-personality-sun-sign"
    assert evidence.claims[0].system == "astrology"
    assert all(claim.dimension in {"personality", "career", "relationship"} for claim in evidence.claims)
    assert evidence.data_quality > 0.5
    assert evidence.claims[2].depends_on == ["astrology-personality-sun-sign"]
    assert evidence.warnings == []
    assert evidence.summary == "星盘启发式分析：太阳星座为双子座，画像完整度为完整。"
    assert evidence.claims[0].statement == "太阳星座为双子座，更容易呈现出与该星座相关的表达风格。"
    assert evidence.claims[0].evidence == ["出生信息：1990-06-12T07:45:00", "太阳星座：双子座"]
    assert evidence.claims[1].evidence == ["季节：夏季", "关注领域：事业、感情"]
    assert evidence.claims[2].evidence == ["画像完整度：完整", "缺失字段：无"]
    assert evidence.claims[1].statement == "出生于夏季，职业倾向更容易围绕表达能见度与主导性展开。"
    assert evidence.claims[0].qualifiers == ["启发式", "象征解释"]
