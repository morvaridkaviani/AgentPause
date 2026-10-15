"""Meta endpoints and stateless evaluation."""

import pytest


def test_health(client):
    body = client.get("/api/v1/health").json()
    assert body["status"] == "ok" and body["simulated_actions_only"] is True


def test_openapi_lists_the_documented_endpoints(client):
    paths = client.get("/api/v1/openapi.json").json()["paths"]
    for path in [
        "/api/v1/evaluate",
        "/api/v1/session",
        "/api/v1/action",
        "/api/v1/intervention",
        "/api/v1/session/{session_id}",
        "/api/v1/session/{session_id}/events",
        "/api/v1/metrics",
        "/api/v1/experiments",
        "/api/v1/experiments/{experiment_id}",
    ]:
        assert path in paths, path


def test_policies_scenarios_and_model(client):
    names = {p["name"] for p in client.get("/api/v1/policies").json()}
    assert {"adaptive", "always_confirm", "full_autonomy", "fixed_threshold", "user_customized"} <= names
    scenarios = client.get("/api/v1/scenarios").json()
    assert [s["id"] for s in scenarios] == ["travel", "email", "shopping", "files", "calendar", "research"]
    travel = client.get("/api/v1/scenarios/travel").json()
    assert travel["steps"] and travel["assumptions"]
    assert client.get("/api/v1/scenarios/atlantis").status_code == 404
    model = client.get("/api/v1/model").json()
    assert model["parameters"]["interruption_cost"] == pytest.approx(0.02)
    assert "IRREVERSIBLE_ACTION" in model["reason_codes"]


BRIEF = {
    "action": "send_email",
    "description": "Send the drafted email to Professor Smith",
    "consequence": "external_communication",
    "reversible": False,
    "intent_confidence": 0.72,
    "agent_confidence": 0.86,
    "task_progress": 0.91,
}


def test_evaluate_brief_example(client):
    r = client.post("/api/v1/evaluate", json={"context": BRIEF})
    assert r.status_code == 200
    d = r.json()
    assert d["decision"] == "ASK_HUMAN" and d["should_ask"] is True
    assert {"LOW_INTENT_CONFIDENCE", "IRREVERSIBLE_ACTION", "EXTERNAL_CONSEQUENCE"} <= set(d["reason_codes"])
    assert d["explanation"] and d["timing"]["why_now"] and d["factors"]
    assert d["recommended_intervention"] == "confirmation"


@pytest.mark.parametrize(
    "policy", ["full_autonomy", "always_confirm", "fixed_threshold", "rule_based", "myopic_voi", "learned"]
)
def test_evaluate_with_each_policy(client, policy):
    r = client.post("/api/v1/evaluate", json={"context": BRIEF, "policy": policy, "explain": "light"})
    assert r.status_code == 200
    assert r.json()["policy"] == policy


def test_evaluate_with_preferences_and_policy_config(client):
    fewer = client.post(
        "/api/v1/evaluate",
        json={
            "context": {**BRIEF, "intent_confidence": 0.95, "agent_confidence": 0.95},
            "preferences": {"profile": "fewer_interruptions"},
        },
    ).json()
    assert fewer["decision"] == "CONTINUE"
    strict = client.post(
        "/api/v1/evaluate",
        json={"context": BRIEF, "policy": {"name": "fixed_threshold", "config": {"threshold": 0.99}}},
    ).json()
    assert strict["decision"] == "CONTINUE"


@pytest.mark.parametrize(
    "body",
    [
        {"context": {"action": "x", "agent_confidence": 1.5}},
        {"context": {"action": ""}},
        {"context": {"action": "x"}, "policy": "telepathy"},
        {"context": {"action": "x"}, "policy": {"name": "fixed_threshold", "config": {"bogus": 1}}},
        {"context": {"action": "x"}, "explain": "verbose"},
        {"context": {"action": "x"}, "preferences": {"profile": "yolo"}},
    ],
)
def test_evaluate_rejects_invalid_input(client, body):
    assert client.post("/api/v1/evaluate", json=body).status_code == 422


def test_evaluate_with_missing_data_and_state(client):
    d = client.post("/api/v1/evaluate", json={"context": {"action": "mystery"}}).json()
    assert "MISSING_SIGNAL_DEFAULTED" in d["reason_codes"]
    state = {"step": 5, "interruption_steps": [1, 2, 3, 4]}
    tired = client.post("/api/v1/evaluate", json={"context": {**BRIEF, "step": 5}, "state": state}).json()
    fresh = client.post("/api/v1/evaluate", json={"context": {**BRIEF, "step": 5}}).json()
    assert tired["terms"]["catch_probability"] < fresh["terms"]["catch_probability"]
