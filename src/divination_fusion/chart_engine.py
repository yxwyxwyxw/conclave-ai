from __future__ import annotations

import logging
from typing import Any

from divination_fusion.models import AnalysisRequest, DataCompleteness, NormalizedProfile
from divination_fusion.mcp_bridge import MCPError, get_bazi_chart, generate_ziwei_chart

logger = logging.getLogger(__name__)

_FOCUS_LABELS = {
    "personality": "性格",
    "career": "事业",
    "relationship": "感情",
    "risk": "风险",
    "health": "健康",
    "wealth": "财务",
}


def resolve_chart_data(
    request: AnalysisRequest,
    profile: NormalizedProfile,
) -> tuple[str, str]:
    """Main entry point: resolve Bazi and Ziwei chart contexts from birth data.

    Returns (bazi_context, ziwei_context) as natural-language text blocks.
    Falls back to heuristic data when MCP is unavailable or birth data is insufficient.
    """
    bazi_ctx = ""
    ziwei_ctx = ""
    if profile.completeness in (DataCompleteness.EXACT, DataCompleteness.ESTIMATED, DataCompleteness.DATE_ONLY):
        if profile.birth_datetime_local:
            bazi_ctx = _resolve_bazi(request, profile)
        else:
            bazi_ctx = _heuristic_bazi_fallback(profile)
        ziwei_ctx = _resolve_ziwei(request, profile)
    else:
        bazi_ctx = _heuristic_bazi_fallback(profile)
        ziwei_ctx = _heuristic_ziwei_fallback(profile)

    if not bazi_ctx.strip():
        bazi_ctx = _heuristic_bazi_fallback(profile)
    if not ziwei_ctx.strip():
        ziwei_ctx = _heuristic_ziwei_fallback(profile)
    return bazi_ctx, ziwei_ctx


def _resolve_bazi(request: AnalysisRequest, profile: NormalizedProfile) -> str:
    raw = profile.birth_datetime_local or ""
    parts = raw.split("T")
    date_part = parts[0]
    time_part = "00:00"
    if len(parts) > 1:
        time_part = parts[1][:5]

    date_bits = date_part.split("-")
    time_bits = time_part.split(":")
    if len(date_bits) != 3 or len(time_bits) < 2:
        return _heuristic_bazi_fallback(profile)

    try:
        year, month, day = int(date_bits[0]), int(date_bits[1]), int(date_bits[2])
        hour, minute = int(time_bits[0]), int(time_bits[1])
    except ValueError:
        return _heuristic_bazi_fallback(profile)

    gender = request.profile.gender or "male"
    city = request.profile.birth_place or profile.birth_place or None

    try:
        chart = get_bazi_chart(
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            gender=gender,
            city=city,
        )
    except MCPError as exc:
        logger.warning("Bazi MCP call failed, using heuristic fallback: %s", exc)
        return _heuristic_bazi_fallback(profile)

    return _format_bazi_chart(chart, request)


def _resolve_ziwei(request: AnalysisRequest, profile: NormalizedProfile) -> str:
    raw = profile.birth_datetime_local or ""
    parts = raw.split("T")
    date_part = parts[0]
    time_part = "00:00"
    if len(parts) > 1:
        time_part = parts[1][:5]

    gender = request.profile.gender or "male"
    if gender in ("男",):
        gender = "male"
    elif gender in ("女",):
        gender = "female"
    name = request.profile.name or profile.name or None

    try:
        result = generate_ziwei_chart(
            name=name,
            gender=gender,
            birth_date=date_part,
            birth_time=time_part,
            birth_location=request.profile.birth_place or profile.birth_place or None,
        )
    except MCPError as exc:
        logger.warning("Ziwei MCP call failed, using heuristic fallback: %s", exc)
        return _heuristic_ziwei_fallback(profile)

    data = result if "success" not in result else result.get("data", result)
    chart = data.get("chart", data)
    return _format_ziwei_chart(chart, request)


def _format_bazi_chart(chart: dict[str, Any], request: AnalysisRequest) -> str:
    lines: list[str] = []
    bazi = chart.get("八字", chart)

    # Basic info
    lines.append(f"四柱：{bazi.get('四柱', '未知')}")
    lines.append(f"日主：{bazi.get('日主', '未知')}")
    lines.append(f"生肖：{bazi.get('生肖', '未知')}")
    lines.append(f"农历：{bazi.get('农历', '未知')}")
    lines.append(f"命宫：{bazi.get('命宫', '未知')}")
    lines.append(f"身宫：{bazi.get('身宫', '未知')}")
    lines.append(f"胎元：{bazi.get('胎元', '未知')}")

    # True solar time
    solar = chart.get("真太阳时")
    if solar:
        lines.append(f"真太阳时：{solar.get('真太阳时', '')}（修正{solar.get('修正分钟', '')}分钟）")

    # Four pillars detail
    pillars = bazi.get("柱位详细", {})
    for key, label in [("年柱", "年"), ("月柱", "月"), ("日柱", "日"), ("时柱", "时")]:
        pillar = pillars.get(key, {})
        if pillar:
            shensha = "、".join(pillar.get("神煞", [])) or "无"
            canggan = "、".join(
                f"{d.get('干', '')}({d.get('五行', '')})" for d in pillar.get("藏干详情", [])
            )
            star_info = pillar.get("主星", "")
            if pillar.get("副星"):
                star_info += f"（副星：{'、'.join(pillar.get('副星', []))}）"
            lines.append(
                f"{label}柱：{pillar.get('干支', '')} "
                f"天干{pillar.get('天干', '')}({pillar.get('五行', '')}) "
                f"地支{pillar.get('地支', '')}"
                f"纳音{pillar.get('纳音', '')} "
                f"十神主星={star_info} "
                f"藏干=[{canggan}] "
                f"神煞=[{shensha}] "
                f"空亡={pillar.get('空亡', '')}"
            )

    # Five elements
    wuxing = bazi.get("五行分值", {})
    if wuxing:
        lines.append(f"五行分值：{wuxing}")

    # Clash/combine/harm
    xch = bazi.get("刑冲合会", {})
    if xch:
        tian = "、".join(xch.get("天干", [])) or "无"
        di = "、".join(xch.get("地支", [])) or "无"
        lines.append(f"刑冲合会 — 天干：{tian}；地支：{di}")

    # Luck cycles (first 5)
    dayun = bazi.get("大运", [])
    if dayun:
        lines.append(f"起运：{bazi.get('起运', '')}（{bazi.get('起运日期', '')}）")
        lines.append("大运：")
        for cycle in dayun[:6]:
            current = "【当前】" if cycle.get("当前") else ""
            lines.append(
                f"  {current}{cycle.get('干支', '')} "
                f"({cycle.get('起始年龄', '')}-{cycle.get('结束年龄', '')}岁, "
                f"{cycle.get('起始年份', '')}-{cycle.get('结束年份', '')}年) "
                f"天干{cycle.get('天干', '')}({cycle.get('天干五行', '')}) "
                f"纳音{cycle.get('纳音', '')} "
                f"主星={cycle.get('主星', '')} "
                f"日主关系={cycle.get('日主关系', '')} "
                f"自坐={cycle.get('自坐', '')} "
                f"星运={cycle.get('星运', '')}"
            )

    # Attribution
    source = chart.get("数据来源", {})
    if source:
        lines.append(f"\n排盘引擎：{source.get('品牌', '')} — {source.get('访问', '')}")

    focus_str = "、".join(_FOCUS_LABELS.get(f, f) for f in request.focus_areas)
    lines.append(f"\n用户提问：{request.query}")
    lines.append(f"关注维度：{focus_str}")

    return "\n".join(lines)


def _format_ziwei_chart(chart: dict[str, Any], request: AnalysisRequest) -> str:
    lines: list[str] = []

    info = chart.get("info", {})
    lines.append(f"姓名：{info.get('name', '未知')}")
    lines.append(f"性别：{info.get('gender', '未知')}")
    lines.append(f"出生日期：{info.get('birthDate', '未知')} {info.get('birthTime', '')}")
    lines.append(f"农历日期：{info.get('lunarDate', '未知')}")
    lines.append(f"命宫：{info.get('destinyPalace', '未知')}")
    lines.append(f"身宫：{info.get('bodyPalace', '未知')}")

    palaces = chart.get("palaces", [])
    if palaces:
        lines.append("\n十二宫：")
        for palace in palaces:
            main_star = palace.get("mainStar", {}).get("name", "") or ""
            stars = [s.get("name", "") for s in palace.get("stars", [])]
            stars_str = "、".join(stars) or "无"
            lines.append(
                f"  {palace.get('name', '')}({palace.get('earthlyBranch', '')}) "
                f"五行={palace.get('element', '')} "
                f"主星={main_star} "
                f"星曜=[{stars_str}] "
                f"亮度={palace.get('brightness', '')} "
                f"强度={palace.get('strength', '')}"
            )

    summary = chart.get("summary", "")
    if summary:
        lines.append(f"\n排盘摘要：{summary}")

    focus_str = "、".join(_FOCUS_LABELS.get(f, f) for f in request.focus_areas)
    lines.append(f"\n用户提问：{request.query}")
    lines.append(f"关注维度：{focus_str}")

    return "\n".join(lines)


def _heuristic_bazi_fallback(profile: NormalizedProfile) -> str:
    completeness = profile.completeness.value
    name = profile.name or "匿名"
    local_dt = profile.birth_datetime_local or "未知"
    tz = profile.timezone
    lines = [
        f"姓名：{name}",
        f"出生时间：{local_dt}（时区：{tz}）",
        f"出生地点：{profile.birth_place or '未知'}",
        f"资料完整度：{completeness}",
    ]
    missing = profile.missing_fields
    if missing:
        lines.append(f"缺失字段：{'、'.join(missing)}")
    notes = profile.notes
    if notes:
        lines.append(f"备注：{'；'.join(notes)}")
    lines.append("\n注意：八字排盘不可用，以上仅为基本信息，分析时请保持保守口径。")
    return "\n".join(lines)


def _heuristic_ziwei_fallback(profile: NormalizedProfile) -> str:
    completeness = profile.completeness.value
    name = profile.name or "匿名"
    local_dt = profile.birth_datetime_local or "未知"
    lines = [
        f"姓名：{name}",
        f"出生时间：{local_dt}",
        f"出生地点：{profile.birth_place or '未知'}",
        f"资料完整度：{completeness}",
    ]
    missing = profile.missing_fields
    if missing:
        lines.append(f"缺失字段：{'、'.join(missing)}")
    lines.append("\n注意：紫微斗数排盘不可用，以上仅为基本信息，分析时请保持保守口径。")
    return "\n".join(lines)
