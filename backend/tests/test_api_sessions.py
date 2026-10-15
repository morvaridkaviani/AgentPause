"""Demo, external-agent, and study sessions."""

import json

import pytest
from api_helpers import drive


def create(client, **body):
    r = client.post("/api/v1/session", json={"mode": "demo", "scenario_id": "travel", "seed": 1, **body})
    assert r.status_code == 201, r.text
    return r.json()


@pytest.mark.parametrize("policy", ["adaptive", "always_confirm", "full_autonomy"])
def test_demo_session_runs_to_completion(client, policy):
    session = create(client, policy=policy)
    assert session["kind"] == "simulated" and session["n_steps"] == 8 and session["brief"]
    assert all(step["label"] for step in session["steps"])
    final = drive(client, session["id"])
    assert final["status"] == "completed"
    assert final["outcome"]["summary"]["policy"] == policy
    decisions = [t["decision"] for t in final["timeline"]]
    if policy == "full_autonomy":
        assert set(decisions) <= {"CONTINUE", "SKIPPED"}
    assert all(t["label"] for t in final["timeline"])
    assert final["timeline"][0]["decision_detail"]["explanation"]


def test_step_returns_decision_and_card(client):
    session = create(client, policy="always_confirm")
    r = client.post(f"/api/v1/session/{session['id']}/step", json={"until": "intervention"}).json()
    assert r["card"] is not None
    card = r["card"]
    for key in ("intervention_id", "action", "decision", "allowed_responses"):
        assert key in card
    assert card["action"]["simulated"] is True
    assert {"approve", "edit", "reject", "ask_why", "cancel_task"} <= set(card["allowed_responses"])
    assert "shown_errors" not in card and "necessary" not in card


def test_conflicts_and_validation(client):
    session = create(client, policy="always_confirm")
    sid = session["id"]
    client.post(f"/api/v1/session/{sid}/step", json={"until": "intervention"})
    assert client.post(f"/api/v1/session/{sid}/step").status_code == 409, "cannot step while a card is open"
    assert client.post("/api/v1/intervention", json={"session_id": sid, "response": "answer"}).status_code == 422
    assert (
        client.post(
            "/api/v1/intervention", json={"session_id": sid, "response": "approve", "intervention_id": "stale"}
        ).status_code
        == 409
    )
    why = client.post("/api/v1/intervention", json={"session_id": sid, "response": "ask_why"}).json()
    assert why["session"]["pending"] is not None, "asking why keeps the card open"
    assert client.post("/api/v1/intervention", json={"session_id": sid, "response": "cancel_task"}).status_code == 200
    assert client.get(f"/api/v1/session/{sid}").json()["status"] == "cancelled"
    assert client.post(f"/api/v1/session/{sid}/step").status_code == 409
    assert client.get("/api/v1/session/nope").status_code == 404
    assert client.post("/api/v1/session", json={"mode": "demo"}).status_code == 422
    assert client.post("/api/v1/session", json={"mode": "demo", "scenario_id": "atlantis"}).status_code == 404


def test_events_and_stream(client):
    session = create(client, policy="adaptive")
    drive(client, session["id"])
    events = client.get(f"/api/v1/session/{session['id']}/events").json()
    types = [e["type"] for e in events]
    assert types[0] == "session_created" and "decision" in types and types[-1] == "completed"
    assert [e["seq"] for e in events] == sorted(e["seq"] for e in events)
    since = client.get(f"/api/v1/session/{session['id']}/events", params={"since": events[-3]["seq"]}).json()
    assert len(since) == 2
    with client.stream("GET", f"/api/v1/session/{session['id']}/stream") as response:
        assert response.headers["content-type"].startswith("text/event-stream")
        body = "".join(response.iter_text())
    assert "event: decision" in body and "event: end" in body


def test_external_agent_session(client):
    session = client.post("/api/v1/session", json={"mode": "api", "policy": "adaptive"}).json()
    assert session["kind"] == "external"
    sid = session["id"]
    low = client.post(
        "/api/v1/action",
        json={"session_id": sid, "context": {"action": "search", "consequence": "read_only", "agent_confidence": 0.95}},
    ).json()
    assert low["decision"]["decision"] == "CONTINUE" and low["intervention_id"] is None
    high = client.post(
        "/api/v1/action",
        json={
            "session_id": sid,
            "context": {
                "action": "send_email",
                "consequence": "external_communication",
                "reversible": False,
                "intent_confidence": 0.7,
            },
        },
    ).json()
    assert high["decision"]["should_ask"] and high["intervention_id"]
    assert high["session"]["status"] == "awaiting_human"
    blocked = client.post("/api/v1/action", json={"session_id": sid, "context": {"action": "x"}})
    assert blocked.status_code == 409
    r = client.post(
        "/api/v1/intervention",
        json={"session_id": sid, "response": "reject", "intervention_id": high["intervention_id"]},
    )
    assert r.status_code == 200 and r.json()["session"]["status"] == "running"
    assert client.post(f"/api/v1/session/{sid}/step").status_code == 409
    events = client.get(f"/api/v1/session/{sid}/events").json()
    assert [e["type"] for e in events].count("decision") == 2


def test_demo_sessions_reject_external_actions(client):
    session = create(client)
    r = client.post("/api/v1/action", json={"session_id": session["id"], "context": {"action": "x"}})
    assert r.status_code == 409


def test_session_listing_and_deletion_require_token_when_configured(secured):
    session = secured.post("/api/v1/session", json={"mode": "demo", "scenario_id": "email", "seed": 2}).json()
    assert secured.get("/api/v1/sessions").status_code == 401
    auth = {"Authorization": "Bearer s3cret"}
    listing = secured.get("/api/v1/sessions", headers=auth).json()
    assert listing["total"] == 1
    assert secured.delete(f"/api/v1/session/{session['id']}").status_code == 401
    assert secured.delete(f"/api/v1/session/{session['id']}", headers=auth).status_code == 204
    assert secured.get(f"/api/v1/session/{session['id']}").status_code == 404


def test_identical_seeds_reproduce_sessions(client):
    a = drive(client, create(client, policy="adaptive", seed=42)["id"])
    b = drive(client, create(client, policy="adaptive", seed=42)["id"])
    strip = lambda s: [(t["label"], t["decision"], t["response"]) for t in s["timeline"]]  # noqa: E731
    assert strip(a) == strip(b)
    assert json.dumps(a["brief"]) == json.dumps(b["brief"])


def test_labelled_policy_specs_work_in_sessions(client):
    spec = {"name": "adaptive", "label": "adaptive@0.03", "parameters": {"interruption_cost": 0.03}}
    demo = client.post("/api/v1/session", json={"mode": "demo", "scenario_id": "email", "policy": spec, "seed": 1})
    assert demo.status_code == 201, demo.text
    assert demo.json()["policy"] == "adaptive@0.03"
    assert client.post(f"/api/v1/session/{demo.json()['id']}/step", json={"until": "intervention"}).status_code == 200

    api = client.post("/api/v1/session", json={"mode": "api", "policy": spec}).json()
    for action, consequence in (("read_inbox", "read_only"), ("archive_thread", "local_modification")):
        r = client.post(
            "/api/v1/action", json={"session_id": api["id"], "context": {"action": action, "consequence": consequence}}
        )
        assert r.status_code == 200, r.text
