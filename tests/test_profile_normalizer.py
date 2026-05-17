from __future__ import annotations

from divination_fusion.agents.intake import build_analysis_request
from divination_fusion.models import DataCompleteness
from divination_fusion.services import normalize_profile


def test_normalize_profile_exact_timezone_conversion() -> None:
    request = build_analysis_request(
        "请分析我的事业",
        name="  Demo User  ",
        birth_date="1990-06-12",
        birth_time="07:45",
        birth_place=" Shanghai ",
        timezone="Asia/Shanghai",
    )

    normalized = normalize_profile(request)

    assert normalized.name == "Demo User"
    assert normalized.timezone == "Asia/Shanghai"
    assert normalized.birth_place == "Shanghai"
    assert normalized.birth_datetime_local == "1990-06-12T07:45:00+08:00"
    assert normalized.birth_datetime_utc == "1990-06-11T23:45:00Z"
    assert normalized.completeness == DataCompleteness.EXACT
    assert normalized.missing_fields == []
    assert normalized.notes == []


def test_normalize_profile_date_only_marks_missing_time() -> None:
    request = build_analysis_request(
        "请分析我的感情",
        birth_date="1990-06-12",
        birth_place="Shanghai",
        timezone="Asia/Shanghai",
    )

    normalized = normalize_profile(request)

    assert normalized.birth_datetime_local == "1990-06-12"
    assert normalized.birth_datetime_utc is None
    assert normalized.completeness == DataCompleteness.DATE_ONLY
    assert normalized.missing_fields == ["birth_time"]
    assert "birth_time_missing_used_date_only_normalization" in normalized.notes


def test_normalize_profile_missing_timezone_defaults_to_utc() -> None:
    request = build_analysis_request(
        "请分析我的事业",
        birth_date="1990-06-12",
        birth_time="07:45",
        birth_place="Shanghai",
    )

    normalized = normalize_profile(request)

    assert normalized.timezone == "UTC"
    assert normalized.birth_datetime_local == "1990-06-12T07:45:00+00:00"
    assert normalized.birth_datetime_utc == "1990-06-12T07:45:00Z"
    assert normalized.completeness == DataCompleteness.ESTIMATED
    assert "timezone_missing_defaulted_to_utc" in normalized.notes
    assert "timezone_assumed_or_fell_back_to_utc" in normalized.notes
    assert "timezone" in normalized.missing_fields


def test_normalize_profile_invalid_timezone_falls_back_to_utc() -> None:
    request = build_analysis_request(
        "请分析我的事业",
        birth_date="1990-06-12",
        birth_time="07:45",
        birth_place="Shanghai",
        timezone="Not/A_Real_Zone",
    )

    normalized = normalize_profile(request)

    assert normalized.timezone == "UTC"
    assert normalized.birth_datetime_local == "1990-06-12T07:45:00+00:00"
    assert normalized.birth_datetime_utc == "1990-06-12T07:45:00Z"
    assert normalized.completeness == DataCompleteness.ESTIMATED
    assert "timezone_invalid_defaulted_to_utc" in normalized.notes


def test_normalize_profile_explicit_utc_is_exact() -> None:
    request = build_analysis_request(
        "请分析我的事业",
        birth_date="1990-06-12",
        birth_time="07:45",
        birth_place="Shanghai",
        timezone="UTC",
    )

    normalized = normalize_profile(request)

    assert normalized.timezone == "UTC"
    assert normalized.birth_datetime_local == "1990-06-12T07:45:00+00:00"
    assert normalized.birth_datetime_utc == "1990-06-12T07:45:00Z"
    assert normalized.completeness == DataCompleteness.EXACT
    assert "timezone_missing_defaulted_to_utc" not in normalized.notes


def test_normalize_profile_missing_birth_date_is_unknown() -> None:
    request = build_analysis_request(
        "请分析我的事业",
        birth_time="07:45",
        birth_place="Shanghai",
        timezone="Asia/Shanghai",
    )

    normalized = normalize_profile(request)

    assert normalized.birth_datetime_local is None
    assert normalized.birth_datetime_utc is None
    assert normalized.completeness == DataCompleteness.UNKNOWN
    assert "birth_date" in normalized.missing_fields
