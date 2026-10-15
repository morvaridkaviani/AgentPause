"""Cross-package integration tests: SDK ↔ REST API ↔ simulator ↔ experiments ↔ examples.

Each package has its own unit tests (sdk/python/tests, simulator/tests, backend/tests). These
tests check that the pieces agree with each other end to end.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from agentpause import AgentPause
from agentpause_sim import ExperimentConfig, run_experiment
from app.config import Settings
from app.main import create_app

ROOT = Path(__file__).resolve().parents[1]

CONTEXT = {
    "action": "send_email",
    "description": "Send the drafted reply",
    "consequence": "external_communication",
    "reversible": False,
    "agent_confidence": 0.86,
    "intent_confidence": 0.72,
    "task_progress": 0.9,
}


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(Settings(database_url="sqlite:///:memory:")))


@pytest.mark.parametrize("policy", ["full_autonomy", "always_confirm", "fixed_threshold", "adaptive", "rule_based"])
def test_rest_api_and_sdk_make_the_same_decision(client: TestClient, policy: str) -> None:
    local = AgentPause(policy=policy).evaluate(**CONTEXT)
    remote = client.post("/api/v1/evaluate", json={"policy": policy, "context": CONTEXT})
    assert remote.status_code == 200, remote.text
    body = remote.json()
    assert body["decision"] == local.decision.value
    assert body["score"] == pytest.approx(local.score, abs=1e-6)  # the API rounds to 6 decimals
    assert body["reason_codes"] == list(local.reason_codes)
    assert body["explanation"] == local.explanation


def test_api_experiment_reproduces_the_simulator_hash(client: TestClient) -> None:
    config = {
        "name": "integration",
        "scenarios": ["email", "files"],
        "policies": ["always_confirm", "adaptive"],
        "episodes": 4,
        "seed": 7,
        "bootstrap": 0,
    }
    direct = run_experiment(ExperimentConfig.from_dict(config))

    created = client.post("/api/v1/experiments", json=config)
    assert created.status_code == 201, created.text
    experiment_id = created.json()["id"]
    for _ in range(200):
        body = client.get(f"/api/v1/experiments/{experiment_id}").json()
        if body["status"] in ("completed", "failed"):
            break
        time.sleep(0.05)
    assert body["status"] == "completed", body.get("error")
    assert body["result"]["result_hash"] == direct.result_hash
    assert body["result"]["note"].startswith("SIMULATED")


def test_demo_session_ground_truth_matches_a_simulated_episode(client: TestClient) -> None:
    """A demo session driven through the API is the same deterministic episode as in the simulator."""
    created = client.post(
        "/api/v1/session", json={"mode": "demo", "scenario_id": "files", "policy": "adaptive", "seed": 11}
    )
    assert created.status_code == 201, created.text
    session_id = created.json()["id"]

    for _ in range(60):
        session = client.get(f"/api/v1/session/{session_id}").json()
        if session["status"] in ("completed", "cancelled"):
            break
        if session["pending"]:
            client.post(
                "/api/v1/intervention",
                json={
                    "session_id": session_id,
                    "response": "approve" if "approve" in session["pending"]["allowed_responses"] else "answer",
                },
            )
        else:
            client.post(f"/api/v1/session/{session_id}/step", json={"until": "next"})
    decisions_api = [item["decision"] for item in session["timeline"]]
    assert session["status"] == "completed"
    assert decisions_api, "the timeline should record decisions"
    assert set(decisions_api) <= {"CONTINUE", "DEFER", "CLARIFY", "ASK_HUMAN", "BLOCK", "SKIPPED"}

    # Same scenario/seed again: identical decisions (determinism across sessions).
    again = client.post(
        "/api/v1/session", json={"mode": "demo", "scenario_id": "files", "policy": "adaptive", "seed": 11}
    ).json()["id"]
    for _ in range(60):
        s2 = client.get(f"/api/v1/session/{again}").json()
        if s2["status"] in ("completed", "cancelled"):
            break
        if s2["pending"]:
            client.post(
                "/api/v1/intervention",
                json={
                    "session_id": again,
                    "response": "approve" if "approve" in s2["pending"]["allowed_responses"] else "answer",
                },
            )
        else:
            client.post(f"/api/v1/session/{again}/step", json={"until": "next"})
    assert [item["decision"] for item in s2["timeline"]] == decisions_api


@pytest.mark.parametrize(
    ("script", "args", "expected"),
    [
        ("examples/python_quickstart.py", [], "ASK_HUMAN"),
        ("examples/guard_decorator.py", ["--yes"], "(simulated) sent"),
    ],
)
def test_examples_run(script: str, args: list[str], expected: str) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / script), *args], capture_output=True, text=True, timeout=120, cwd=ROOT
    )
    assert result.returncode == 0, result.stderr
    assert expected in result.stdout


def test_experiment_scripts_run_and_are_deterministic(tmp_path: Path) -> None:
    hashes = []
    for run in ("a", "b"):
        out = tmp_path / run
        result = subprocess.run(
            [sys.executable, str(ROOT / "experiments" / "compare_policies.py"), "--episodes", "2", "--out", str(out)],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=ROOT,
        )
        assert result.returncode == 0, result.stderr
        assert "SIMULATED RESULTS" in result.stdout
        assert (out / "hypotheses.json").exists()
        hashes.append(__import__("json").loads((out / "summary.json").read_text())["result_hash"])
    assert hashes[0] == hashes[1]


def test_browser_demo_bridge_serves_the_real_api() -> None:
    """scripts/static_demo/agentpause_web.py is what the GitHub Pages demo runs in Pyodide."""
    import asyncio
    import importlib.util
    import json

    import anyio.to_thread

    original = anyio.to_thread.run_sync
    try:
        spec = importlib.util.spec_from_file_location(
            "agentpause_web", ROOT / "scripts" / "static_demo" / "agentpause_web.py"
        )
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        def call(method: str, path: str, query: str = "", body: dict | None = None) -> tuple[int, object]:
            raw = json.loads(asyncio.run(module.handle(method, path, query, json.dumps(body) if body else None)))
            content = json.loads(raw["body"]) if raw["contentType"].startswith("application/json") else raw["body"]
            return raw["status"], content

        status, health = call("GET", "/api/v1/health")
        assert status == 200 and health["environment"] == "browser-demo"
        status, session = call(
            "POST", "/api/v1/session", body={"mode": "demo", "scenario_id": "email", "policy": "adaptive", "seed": 3}
        )
        assert status == 201
        status, stepped = call("POST", f"/api/v1/session/{session['id']}/step", body={"until": "intervention"})
        assert status == 200 and stepped["session"]["status"] in ("awaiting_human", "completed")
        status, csv_text = call("GET", "/api/v1/events", "format=csv")
        assert status == 200 and str(csv_text).startswith("id,")
        status, _ = call("GET", "/api/v1/session/nope")
        assert status == 404
    finally:
        anyio.to_thread.run_sync = original
