from __future__ import annotations

import time

from fastapi.testclient import TestClient

from divination_fusion.adapters import AdapterError, AdapterRegistry, ModelAdapter, ModelRequest
from divination_fusion.session_store import SessionStore
from divination_fusion.web_ui import APP_HTML
from divination_fusion.webapp import _run_session_thread, create_app


class ScenarioAdapter(ModelAdapter):
    provider_name = "fake"

    def __init__(self, scenario: str) -> None:
        self.scenario = scenario
        self.call_counts: dict[tuple[str, str, int], int] = {}

    def _call_model(self, request: ModelRequest, *, correction_prompt: str | None) -> str:
        round_index = int(request.runtime_constraints.get("round_index", 0) or 0)
        phase = str(request.runtime_constraints.get("phase", ""))
        key = (request.schema_name, request.system_name, round_index)
        self.call_counts[key] = self.call_counts.get(key, 0) + 1

        if request.role == "analyzer":
            if self.scenario == "single-sided" and request.system_name == "ziwei":
                raise AdapterError("ziwei unavailable")
            return (
                f"【结论】\n{request.system_name} 对问题给出了一版完整分析。\n\n"
                "【分析】\n"
                + (
                    "八字认为 26 年挣钱，27 年亏欠。"
                    if request.system_name == "bazi"
                    else "紫微认为 26 年和 27 年都挣钱。"
                )
                + "\n\n【依据】\nmock evidence\n\n【保留】\n当前仅作测试。"
            )
        if request.role == "battler":
            if self.scenario == "always-invalid":
                raise AdapterError("mock battler failure")
            return f"{request.system_name} 第 {round_index or 1} 轮继续围绕 27 年财运回应对方。"

        if phase == "issue-detection":
            return (
                "[议题1]\n"
                "维度：wealth\n"
                "标题：27 年财运判断\n"
                "关系：contradiction\n"
                "八字立场：27 年亏欠\n"
                "紫微立场：27 年挣钱\n"
                "裁判发问：八字认为 27 年亏欠，紫微认为 27 年挣钱，你们分别回应对方。\n"
                "控题边界：只讨论 27 年财运，不要扩展到别的话题。\n"
            )

        if phase == "moderation":
            if self.scenario == "converged":
                return (
                    "[回合裁定]\n"
                    "当前状态：结束\n"
                    "裁判意见：双方已经围绕 27 年财运完成回应，可以结束当前争论。\n"
                    "下一轮问题：\n"
                    "终止原因：mutual-convergence\n"
                )
            return (
                "[回合裁定]\n"
                "当前状态：继续\n"
                "裁判意见：继续围绕 27 年财运，不要扩展。\n"
                "下一轮问题：请继续只讨论 27 年财运，并直接回应对方。\n"
                "终止原因：\n"
            )

        return (
            "[终局裁决]\n"
            "裁决类型：conditional\n"
            "偏向体系：bazi\n"
            "裁决摘要：当前更偏向八字，但仍需保留边界。\n"
            "裁决理由：裁判认为当前更偏向八字，但保留条件边界。\n"
            "保留条件：\n"
            "- fake judge\n"
        )


def _make_client(tmp_path, scenario: str) -> TestClient:
    registry = AdapterRegistry({"fake": ScenarioAdapter(scenario)})
    store = SessionStore(root=tmp_path / "sessions", database_path=tmp_path / "sessions.sqlite3")
    app = create_app(store=store, adapters=registry)
    return TestClient(app)


def _login(client: TestClient) -> None:
    response = client.post("/api/login", json={"password": "changeme"})
    assert response.status_code == 200


def _payload(scenario: str = "max-rounds") -> dict[str, object]:
    provider = "fake"
    return {
        "query": "请综合分析我的事业和感情趋势",
        "name": "Demo",
        "birth_date": "1990-06-12",
        "birth_time": "07:45",
        "birth_place": "Shanghai",
        "timezone": "Asia/Shanghai",
        "max_battle_rounds": 4,
        "credential_mode": "byok" if scenario == "byok" else "server",
        "openai_api_key": "user-openai-key" if scenario == "byok" else None,
        "openrouter_api_key": "user-openrouter-key" if scenario == "byok" else None,
        "anthropic_api_key": "user-anthropic-key" if scenario == "byok" else None,
        "provider_configs": {
            "bazi_analyzer": {"provider": provider, "model": "fake-model"},
            "ziwei_analyzer": {"provider": provider, "model": "fake-model"},
            "bazi_battler": {"provider": provider, "model": "fake-model"},
            "ziwei_battler": {"provider": provider, "model": "fake-model"},
            "judge": {"provider": provider, "model": "fake-model"},
        },
    }


def _wait_for_terminal(client: TestClient, session_id: str) -> dict[str, object]:
    for _ in range(40):
        payload = client.get(f"/api/sessions/{session_id}").json()
        if payload["status"] in {"completed", "failed", "cancelled"}:
            return payload
        time.sleep(0.05)
    raise AssertionError("session did not finish in time")


def test_api_requires_login(tmp_path):
    client = _make_client(tmp_path, "max-rounds")

    response = client.get("/api/sessions")

    assert response.status_code == 401


def test_index_page_reserves_dual_channel_and_aux_fields(tmp_path):
    client = _make_client(tmp_path, "max-rounds")

    response = client.get("/")

    assert response.status_code == 200
    assert "尚未开始辩论" in response.text
    assert "public_response" in APP_HTML
    assert "命理裁决台" in response.text
    assert "争议裁决" in response.text


def test_webapp_can_create_replay_and_stream_session(tmp_path):
    client = _make_client(tmp_path, "max-rounds")
    _login(client)

    create = client.post("/api/sessions", json=_payload())
    assert create.status_code == 200
    session_id = create.json()["session_id"]

    finished = _wait_for_terminal(client, session_id)
    assert finished["status"] == "completed"
    assert finished["snapshot"]["fusion_report"]["summary"]
    issues = finished["snapshot"]["debate_issues"]
    assert any(
        issue["termination_reason"] in {"max-rounds-reached", "stability-stop"}
        for issue in issues
    )

    with client.stream("GET", f"/api/sessions/{session_id}/events") as response:
        body = "".join(chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk for chunk in response.iter_text())
    assert "session_started" in body
    assert "report_ready" in body


def test_byok_keys_are_not_persisted(tmp_path):
    client = _make_client(tmp_path, "max-rounds")
    _login(client)

    create = client.post("/api/sessions", json=_payload("byok"))
    session_id = create.json()["session_id"]
    finished = _wait_for_terminal(client, session_id)

    assert finished["request_payload"]["openai_api_key"] is None
    assert finished["request_payload"]["openrouter_api_key"] is None
    assert finished["request_payload"]["anthropic_api_key"] is None
    request_path = tmp_path / "sessions" / session_id / "request.json"
    assert "user-openai-key" not in request_path.read_text(encoding="utf-8")
    assert "user-openrouter-key" not in request_path.read_text(encoding="utf-8")
    assert "user-anthropic-key" not in request_path.read_text(encoding="utf-8")


def test_battle_can_converge_early(tmp_path):
    client = _make_client(tmp_path, "converged")
    _login(client)

    create = client.post("/api/sessions", json=_payload())
    session_id = create.json()["session_id"]
    finished = _wait_for_terminal(client, session_id)

    issues = finished["snapshot"]["debate_issues"]
    assert any(issue["termination_reason"] == "mutual-convergence" for issue in issues)
    assert any(issue["status"] == "resolved" for issue in issues)


def test_invalid_json_can_repair_and_continue(tmp_path):
    client = _make_client(tmp_path, "repair-once")
    _login(client)

    create = client.post("/api/sessions", json=_payload())
    session_id = create.json()["session_id"]
    finished = _wait_for_terminal(client, session_id)

    assert finished["status"] == "completed"
    assert finished["snapshot"]["judgements"]


def test_round_failure_escalates_to_judge(tmp_path):
    client = _make_client(tmp_path, "always-invalid")
    _login(client)

    create = client.post("/api/sessions", json=_payload())
    session_id = create.json()["session_id"]
    finished = _wait_for_terminal(client, session_id)

    assert finished["status"] == "completed"
    issues = finished["snapshot"]["debate_issues"]
    assert any(issue["termination_reason"] == "model-round-failed" for issue in issues)
    judgements = finished["snapshot"]["judgements"]
    assert any("未返回有效文本" in " ".join(item["conditions"]) for item in judgements)


def test_single_sided_issue_skips_multi_party_battle(tmp_path):
    client = _make_client(tmp_path, "single-sided")
    _login(client)

    create = client.post("/api/sessions", json=_payload())
    session_id = create.json()["session_id"]
    finished = _wait_for_terminal(client, session_id)

    issues = finished["snapshot"]["debate_issues"]
    assert not issues or all(issue["termination_reason"] in {None, "single-sided-issue"} for issue in issues)


def test_run_session_thread_marks_failed_when_exception_escapes(tmp_path):
    store = SessionStore(root=tmp_path / "sessions", database_path=tmp_path / "sessions.sqlite3")
    store.create_session(session_id="sess001", request_payload={"query": "demo"}, auth_mode="server")
    store.update_snapshot(session_id="sess001", status="running", snapshot={"phase": "started"})

    class BrokenOrchestrator:
        def __init__(self, store):
            self.store = store

        def run(self, session_id, run_input, cancel_event=None):
            raise RuntimeError("boom")

    _run_session_thread(BrokenOrchestrator(store), "sess001", None, None)

    record = store.get_session("sess001")
    events = store.list_events("sess001")

    assert record.status == "failed"
    assert events[-1].event_type == "session_failed"
    assert events[-1].payload["error"] == "boom"
