from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from divination_fusion.models import AnalysisRequest, Claim, NormalizedProfile, SystemEvidence

SYSTEM_NAME = "astrology"
PROMPT_VERSION = "astrology-heuristic-v1"
FOCUS_AREA_LABELS = {
    "personality": "性格",
    "career": "事业",
    "relationship": "感情",
    "risk": "风险",
}
SUN_SIGN_LABELS = {
    "Aries": "白羊座",
    "Taurus": "金牛座",
    "Gemini": "双子座",
    "Cancer": "巨蟹座",
    "Leo": "狮子座",
    "Virgo": "处女座",
    "Libra": "天秤座",
    "Scorpio": "天蝎座",
    "Sagittarius": "射手座",
    "Capricorn": "摩羯座",
    "Aquarius": "水瓶座",
    "Pisces": "双鱼座",
    "Unknown": "未知",
}
SEASON_LABELS = {
    "spring": "春季",
    "summer": "夏季",
    "autumn": "秋季",
    "winter": "冬季",
    "unknown season": "未知季节",
}
COMPLETENESS_LABELS = {
    "exact": "完整",
    "estimated": "估计",
    "date-only": "仅日期",
    "unknown": "未知",
}
MISSING_FIELD_LABELS = {
    "birth_date": "出生日期",
    "birth_time": "出生时辰",
    "birth_place": "出生地点",
    "timezone": "时区",
}

ZODIAC_WINDOWS: list[tuple[tuple[int, int], str]] = [
    ((1, 20), "Aquarius"),
    ((2, 19), "Pisces"),
    ((3, 21), "Aries"),
    ((4, 20), "Taurus"),
    ((5, 21), "Gemini"),
    ((6, 21), "Cancer"),
    ((7, 23), "Leo"),
    ((8, 23), "Virgo"),
    ((9, 23), "Libra"),
    ((10, 23), "Scorpio"),
    ((11, 22), "Sagittarius"),
    ((12, 22), "Capricorn"),
]


def analyze_astrology(request: AnalysisRequest, profile: NormalizedProfile) -> SystemEvidence:
    birth_dt = _parse_local_datetime(profile.birth_datetime_local, profile.timezone)
    sun_sign = _sun_sign(birth_dt.date() if birth_dt else None)
    season = _season_for_date(birth_dt.date() if birth_dt else None)
    sun_sign_label = SUN_SIGN_LABELS.get(sun_sign, sun_sign)
    season_label = SEASON_LABELS[season]
    completeness_label = COMPLETENESS_LABELS.get(profile.completeness.value, profile.completeness.value)

    claims = [
        Claim(
            claim_id="astrology-personality-sun-sign",
            system=SYSTEM_NAME,
            dimension="personality",
            statement=f"太阳星座为{sun_sign_label}，更容易呈现出与该星座相关的表达风格。",
            evidence=[f"出生信息：{profile.birth_datetime_local or profile.name or '未知'}", f"太阳星座：{sun_sign_label}"],
            qualifiers=["启发式", "象征解释"],
        ),
        Claim(
            claim_id="astrology-career-season",
            system=SYSTEM_NAME,
            dimension="career",
            statement=f"出生于{season_label}，职业倾向更容易围绕{_career_tone(season)}展开。",
            evidence=[f"季节：{season_label}", f"关注领域：{_join_focus_areas(request.focus_areas)}"],
            qualifiers=["启发式"],
        ),
        Claim(
            claim_id="astrology-relationship-focus",
            system=SYSTEM_NAME,
            dimension="relationship",
            statement=_relationship_statement(profile, request),
            evidence=[f"画像完整度：{completeness_label}", f"缺失字段：{_join_missing_fields(profile.missing_fields)}"],
            depends_on=["astrology-personality-sun-sign"],
            qualifiers=["条件判断"],
        ),
    ]

    warnings = _build_warnings(profile, birth_dt)
    data_quality = _data_quality(profile, birth_dt)
    summary = f"星盘启发式分析：太阳星座为{sun_sign_label}，画像完整度为{completeness_label}。"

    return SystemEvidence(
        system=SYSTEM_NAME,
        summary=summary,
        claims=claims,
        data_quality=data_quality,
        warnings=warnings,
    )


def _parse_local_datetime(local_value: Optional[str], timezone: str) -> Optional[datetime]:
    if not local_value:
        return None
    try:
        value = datetime.fromisoformat(local_value)
    except ValueError:
        return None
    try:
        zone = ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        zone = ZoneInfo("UTC")
    if value.tzinfo is not None:
        return value.astimezone(zone)
    return value.replace(tzinfo=zone)


def _sun_sign(birth_date: Optional[date]) -> str:
    if birth_date is None:
        return "Unknown"
    month_day = (birth_date.month, birth_date.day)
    for boundary, sign in reversed(ZODIAC_WINDOWS):
        if month_day >= boundary:
            return sign
    return "Capricorn"


def _season_for_date(birth_date: Optional[date]) -> str:
    if birth_date is None:
        return "unknown season"
    month = birth_date.month
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    if month in (9, 10, 11):
        return "autumn"
    return "winter"


def _career_tone(season: str) -> str:
    return {
        "spring": "试错增长与持续展开",
        "summer": "表达能见度与主导性",
        "autumn": "结构整理与打磨",
        "winter": "规划收拢与沉淀",
        "unknown season": "弹性适配",
    }.get(season, "弹性适配")


def _relationship_statement(profile: NormalizedProfile, request: AnalysisRequest) -> str:
    if profile.birth_datetime_local and "relationship" in request.focus_areas:
        return "当关系议题被明确关注时，更适合用稳定沟通和边界感来解释感情走势。"
    return "关系议题目前更偏概括性判断，建议补全时辰后再细化。"


def _build_warnings(profile: NormalizedProfile, birth_dt: Optional[datetime]) -> list[str]:
    warnings: list[str] = []
    if birth_dt is None:
        warnings.append("出生时间不完整，星盘相关主张会转为更保守的表达。")
    if profile.completeness.value in {"date-only", "unknown"}:
        warnings.append("时辰敏感的解释已主动降调。")
    return warnings


def _data_quality(profile: NormalizedProfile, birth_dt: Optional[datetime]) -> float:
    base = {
        "exact": 0.92,
        "estimated": 0.75,
        "date-only": 0.52,
        "unknown": 0.35,
    }.get(profile.completeness.value, 0.35)
    if birth_dt is None:
        base -= 0.08
    return max(0.0, min(1.0, base))


def _join_focus_areas(focus_areas: list[str]) -> str:
    if not focus_areas:
        return "无"
    return "、".join(FOCUS_AREA_LABELS.get(area, area) for area in focus_areas)


def _join_missing_fields(missing_fields: list[str]) -> str:
    if not missing_fields:
        return "无"
    return "、".join(MISSING_FIELD_LABELS.get(field, field) for field in missing_fields)
