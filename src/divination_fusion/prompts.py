from __future__ import annotations

from pathlib import Path

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


def _load(name: str, **kwargs: object) -> str:
    """Read a template file and format it with the given kwargs."""
    path = _TEMPLATES_DIR / f"{name}.txt"
    template = path.read_text(encoding="utf-8")
    if kwargs:
        template = template.format(**{k: v for k, v in kwargs.items() if v is not None})
    return template


# -- system prompts ----------------------------------------------------------

def analyzer_system_prompt(system_name: str) -> str:
    try:
        return _load(f"system_analyzer_{system_name}")
    except FileNotFoundError:
        return _load("system_analyzer_default", system_name=system_name)


def battler_system_prompt(system_name: str) -> str:
    try:
        return _load(f"system_battler_{system_name}")
    except FileNotFoundError:
        return _load("system_battler_default", system_name=system_name)


def judge_system_prompt() -> str:
    return _load("system_judge")


# -- user prompts ------------------------------------------------------------

def analyzer_user_prompt_with_chart(
    query: str,
    focus_areas: list[str],
    system_name: str,
    chart_context: str,
) -> str:
    system_label = "八字" if system_name == "bazi" else "紫微斗数"
    if system_name == "bazi":
        extra_instruction = (
            "**重要**：排盘数据中已包含大运信息。你必须在分析中明确结合当前大运（标注了【当前】的那个），"
            "说明当前大运的天干地支、十神关系如何影响用户问题。也要对比前后大运的转折。\n"
        )
    else:
        extra_instruction = (
            "**重要**：排盘数据中已包含十二宫星曜配置。你必须在分析中明确结合命盘结构，"
            "推断当前人生阶段的运势趋势。紫微排盘暂无大限数据，但你可以根据命宫、身宫和各大限的"
            "三方四正关系，推测用户当前所处的大限区间可能的影响。\n"
        )
    return _load(
        "user_analyzer_chart",
        query=query,
        focus_areas="、".join(focus_areas) if focus_areas else "未显式指定",
        system_label=system_label,
        chart_context=chart_context,
        extra_instruction=extra_instruction,
    )
