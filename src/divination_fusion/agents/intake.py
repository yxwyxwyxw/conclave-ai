from __future__ import annotations

from typing import Optional

from divination_fusion.models import AnalysisRequest, PersonProfile


def build_analysis_request(
    query: str,
    *,
    name: Optional[str] = None,
    birth_date: Optional[str] = None,
    birth_time: Optional[str] = None,
    birth_place: Optional[str] = None,
    timezone: Optional[str] = None,
    focus_areas: Optional[list[str]] = None,
    output_style: str = "concise",
    metadata: Optional[dict[str, object]] = None,
) -> AnalysisRequest:
    focus = focus_areas or infer_focus_areas(query)
    profile = PersonProfile(
        name=name,
        birth_date=birth_date,
        birth_time=birth_time,
        birth_place=birth_place,
        timezone=timezone,
    )
    return AnalysisRequest(
        query=query.strip(),
        profile=profile,
        focus_areas=focus,
        output_style=output_style,
        metadata=dict(metadata or {}),
    )


def infer_focus_areas(query: str) -> list[str]:
    keyword_map = {
        "感情": "relationship",
        "恋爱": "relationship",
        "婚姻": "relationship",
        "事业": "career",
        "工作": "career",
        "财运": "wealth",
        "健康": "health",
        "性格": "personality",
    }
    focus = []
    for keyword, dimension in keyword_map.items():
        if keyword in query and dimension not in focus:
            focus.append(dimension)
    return focus or ["personality", "career", "relationship"]
