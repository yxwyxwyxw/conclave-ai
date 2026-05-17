from __future__ import annotations

import json
from pathlib import Path

from divination_fusion.agents import build_analysis_request
from divination_fusion.trace import TraceRecorder, load_trace_metadata
from divination_fusion.workflow import replay_trace, run_analysis


def test_trace_recorder_writes_atomic_artifacts(tmp_path: Path) -> None:
    recorder = TraceRecorder.create(tmp_path)
    recorder.record(
        "normalize_profile",
        {"query": "test"},
        {"status": "ok"},
        prompt_version="prompt-v1",
        model_version="code",
        rule_version="rules-v1",
        metadata={"summary_length": 2},
    )

    run_dir = recorder.root
    assert (run_dir / "normalize_profile.input.json").is_file()
    assert (run_dir / "normalize_profile.output.json").is_file()
    assert (run_dir / "trace_metadata.json").is_file()

    metadata = load_trace_metadata(run_dir)
    assert metadata.run_id == recorder.metadata.run_id
    assert metadata.steps[0].step == "normalize_profile"
    assert metadata.steps[0].metadata == {"summary_length": 2}

    metadata_payload = json.loads((run_dir / "trace_metadata.json").read_text(encoding="utf-8"))
    assert metadata_payload["steps"][0]["step"] == "normalize_profile"


def test_replay_trace_returns_structured_summary(tmp_path: Path) -> None:
    request = build_analysis_request(
        "请综合分析我的事业和感情趋势",
        name="Smoke Test",
        birth_date="1990-06-12",
        birth_time="07:45",
        birth_place="Shanghai",
        timezone="Asia/Shanghai",
    )

    state = run_analysis(request, trace_root=tmp_path)
    assert state.trace_metadata is not None

    replay = replay_trace(tmp_path / state.trace_metadata.run_id)

    assert replay["run_id"] == state.trace_metadata.run_id
    assert replay["step_count"] == 5
    assert replay["step_names"] == [
        "normalize_profile",
        "analyzers",
        "battle",
        "judge",
        "report",
    ]
    assert replay["metadata"]["steps"][0]["input_ref"] == "normalize_profile.input.json"
    assert replay["metadata_text"].startswith("{")
