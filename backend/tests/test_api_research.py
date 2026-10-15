"""Comparisons, experiments, metrics, event log, exports."""

import csv
import io
import time

from api_helpers import drive


def test_quick_compare(client):
    body = {
        "scenarios": ["email", "shopping"],
        "policies": ["full_autonomy", "always_confirm", "adaptive"],
        "episodes": 5,
        "trace_scenario": "email",
    }
    r = client.post("/api/v1/compare", json=body)
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["note"].startswith("SIMULATED")
    assert {a["policy"] for a in out["aggregates"]} == {"full_autonomy", "always_confirm", "adaptive"}
    assert set(out["traces"]) == {"full_autonomy", "always_confirm", "adaptive"}
    trace = out["traces"]["always_confirm"]
    assert trace["steps"] and "summary" in trace["outcome"]
    assert any(c["baseline"] == "always_confirm" for c in out["comparisons"])


def test_compare_limits(client):
    r = client.post("/api/v1/compare", json={"episodes": 300, "policies": ["adaptive"] * 3})
    assert r.status_code == 422


def _experiment(client, **overrides):
    body = {
        "name": "test run",
        "scenarios": ["email"],
        "policies": [
            "always_confirm",
            "adaptive",
            {"name": "adaptive", "label": "cheap", "parameters": {"interruption_cost": 0.005}},
        ],
        "episodes": 4,
        "bootstrap": 20,
        **overrides,
    }
    return client.post("/api/v1/experiments", params={"wait": True}, json=body)


def test_experiment_lifecycle_and_export(client):
    r = _experiment(client)
    assert r.status_code == 201, r.text
    exp = r.json()
    assert exp["status"] == "completed", exp["error"]
    assert exp["progress"] == {"done": 12, "total": 12}
    policies = {a["policy"] for a in exp["result"]["aggregates"]}
    assert policies == {"always_confirm", "adaptive", "cheap"}
    assert exp["result"]["note"].startswith("SIMULATED")
    assert client.get(f"/api/v1/experiments/{exp['id']}").json()["status"] == "completed"
    assert any(e["id"] == exp["id"] for e in client.get("/api/v1/experiments").json())
    records = client.get(f"/api/v1/experiments/{exp['id']}/export", params={"table": "records", "format": "csv"})
    rows = list(csv.DictReader(io.StringIO(records.text)))
    assert rows and {"participant_id", "policy", "decision", "task_success", "subjective_rating"} <= set(rows[0])
    episodes = client.get(
        f"/api/v1/experiments/{exp['id']}/export", params={"table": "episodes", "format": "json"}
    ).json()
    assert len(episodes) == 12
    assert client.get(f"/api/v1/experiments/{exp['id']}/export", params={"table": "summary"}).json()["result"]
    assert client.delete(f"/api/v1/experiments/{exp['id']}").status_code == 204
    assert client.get(f"/api/v1/experiments/{exp['id']}").status_code == 404


def test_experiment_validation(client):
    assert _experiment(client, scenarios=["atlantis"]).status_code == 404
    assert _experiment(client, policies=["telepathy"]).status_code == 422
    assert _experiment(client, episodes=2000, scenarios=["all"]).status_code == 422
    assert client.post("/api/v1/experiments", json={"name": "x", "policies": []}).status_code == 422


def test_background_experiment_completes(client):
    exp = client.post(
        "/api/v1/experiments", json={"name": "bg", "scenarios": ["files"], "policies": ["adaptive"], "episodes": 3}
    ).json()
    for _ in range(100):
        status = client.get(f"/api/v1/experiments/{exp['id']}").json()["status"]
        if status in ("completed", "failed"):
            break
        time.sleep(0.05)
    assert status == "completed"


def test_metrics_from_experiment_with_filters(client):
    exp = _experiment(client).json()
    m = client.get("/api/v1/metrics").json()
    assert m["source"] == "experiment" and m["filters"]["experiment_id"] == exp["id"]
    assert m["n_episodes"] == 12
    charts = m["charts"]
    for key in ("decisions_by_policy", "intervention_timing", "reasons", "risk", "uncertainty", "summary"):
        assert key in charts
    assert {row["bin"] for row in charts["intervention_timing"]} == {"0–20%", "20–40%", "40–60%", "60–80%", "80–100%"}
    only = client.get("/api/v1/metrics", params={"policy": "adaptive", "risk": "high"}).json()
    assert only["n_episodes"] == 4
    assert {r["policy"] for r in only["charts"]["risk"]} <= {"adaptive"}
    assert all(r["risk_level"] == "high" for r in only["charts"]["risk"])
    assert m["metric_definitions"]


def test_metrics_from_sessions(client):
    for policy in ("adaptive", "always_confirm"):
        s = client.post(
            "/api/v1/session", json={"mode": "demo", "scenario_id": "email", "policy": policy, "seed": 3}
        ).json()
        drive(client, s["id"])
    m = client.get("/api/v1/metrics", params={"source": "sessions"}).json()
    assert m["n_episodes"] == 2
    assert {a["policy"] for a in m["aggregates"]} == {"adaptive", "always_confirm"}
    assert client.get("/api/v1/metrics", params={"source": "sessions", "policy": "adaptive"}).json()["n_episodes"] == 1


def test_event_log_filters_and_csv(client):
    s = client.post(
        "/api/v1/session", json={"mode": "demo", "scenario_id": "calendar", "policy": "always_confirm", "seed": 5}
    ).json()
    drive(client, s["id"])
    log = client.get("/api/v1/events", params={"session_id": s["id"], "limit": 5}).json()
    assert log["total"] > 5 and len(log["items"]) == 5
    decisions = client.get("/api/v1/events", params={"type": "decision", "decision": "ASK_HUMAN"}).json()
    assert decisions["items"] and all(e["decision"] == "ASK_HUMAN" for e in decisions["items"])
    interventions = client.get("/api/v1/events", params={"interventions_only": True}).json()
    assert all(e["intervention"] for e in interventions["items"])
    csv_text = client.get("/api/v1/events", params={"format": "csv"}).text
    header = csv_text.splitlines()[0]
    assert header.startswith("id,seq,session_id")
    assert "payload" not in header


def test_researcher_endpoints_are_protected(secured):
    assert secured.get("/api/v1/events").status_code == 401
    assert secured.get("/api/v1/events", headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert secured.get("/api/v1/events", headers={"Authorization": "Bearer s3cret"}).status_code == 200
    assert secured.get("/api/v1/metrics").status_code == 200, "aggregate metrics stay public"
