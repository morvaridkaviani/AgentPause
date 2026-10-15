"""Study mode."""

from itertools import pairwise

import pytest
from api_helpers import drive

from app.services.study import williams_square


@pytest.mark.parametrize("n", [2, 3, 4, 5, 6])
def test_williams_square_is_a_balanced_latin_square(n):
    rows = williams_square(n)
    assert len(rows) == (n if n % 2 == 0 else 2 * n)
    for row in rows:
        assert sorted(row) == list(range(n))
    for col in range(n):
        column = [row[col] for row in rows[:n]]
        assert sorted(column) == list(range(n))
    # first-order carry-over balance: each ordered pair (a, b) appears equally often
    counts: dict[tuple[int, int], int] = {}
    for row in rows:
        for a, b in pairwise(row):
            counts[(a, b)] = counts.get((a, b), 0) + 1
    assert len(set(counts.values())) == 1
    assert len(counts) == n * (n - 1)


def enrol(client):
    p = client.post("/api/v1/study/participants").json()
    client.patch(f"/api/v1/study/participants/{p['code']}", json={"consented": True})
    return p


def test_participants_are_counterbalanced(client):
    ps = [client.post("/api/v1/study/participants").json() for _ in range(8)]
    assert len({p["code"] for p in ps}) == 8
    assert all(p["code"].startswith("P-") for p in ps)
    first = ps[0]["plan"]
    assert first[0]["practice"] is True
    orders = [tuple(b["policy"] for b in p["plan"][1:]) for p in ps[:4]]
    assert len(set(orders)) == 4
    for position in range(4):
        assert len({o[position] for o in orders}) == 4, "each condition appears once per position"
    modes = [p["explanation_mode"] for p in ps[:4]]
    assert sorted(modes) == ["factors", "full", "none", "placebo"]
    for p in ps[:4]:
        scenarios = [b["scenario_id"] for b in p["plan"][1:]]
        assert len(set(scenarios)) == 4


def test_assignment_crosses_orders_modes_and_scenarios(client):
    """Default design: 4 conditions × 4 scenarios × 4 explanation modes."""
    from collections import Counter

    ps = [client.post("/api/v1/study/participants").json() for _ in range(16)]
    orders = [tuple(b["policy"] for b in p["plan"][1:]) for p in ps]
    # Every explanation mode receives every condition order exactly once per 16 participants.
    by_mode: dict[str, set[tuple[str, ...]]] = {}
    for p, order in zip(ps, orders, strict=True):
        by_mode.setdefault(p["explanation_mode"], set()).add(order)
    assert len(by_mode) == 4
    assert all(len(o) == 4 for o in by_mode.values())
    # Policy × scenario pairs are balanced within every run of 4 participants.
    for start in range(0, 16, 4):
        pairs = Counter((b["policy"], b["scenario_id"]) for p in ps[start : start + 4] for b in p["plan"][1:])
        assert len(pairs) == 16 and set(pairs.values()) == {1}
    # Scenario offsets rotate, so a scenario is not tied to a block position.
    first_scenarios = {p["plan"][1]["scenario_id"] for p in ps}
    assert len(first_scenarios) == 4


def test_consent_is_required_before_sessions(client):
    p = client.post("/api/v1/study/participants").json()
    r = client.post("/api/v1/study/sessions", json={"participant_code": p["code"], "block": 1})
    assert r.status_code == 403
    client.patch(f"/api/v1/study/participants/{p['code']}", json={"consented": True})
    r = client.post("/api/v1/study/sessions", json={"participant_code": p["code"], "block": 1})
    assert r.status_code == 201
    assert client.post("/api/v1/study/sessions", json={"participant_code": p["code"], "block": 99}).status_code == 422
    assert client.post("/api/v1/study/sessions", json={"participant_code": "P-NOPE00", "block": 1}).status_code == 404


def _participant_with_mode(client, mode):
    for _ in range(8):
        p = enrol(client)
        if p["explanation_mode"] == mode:
            return p
    raise AssertionError(mode)


@pytest.mark.parametrize("mode", ["none", "placebo", "factors", "full"])
def test_study_sessions_apply_explanation_condition_and_hide_ground_truth(client, mode):
    p = _participant_with_mode(client, mode)
    block = p["plan"][1]
    session = client.post("/api/v1/study/sessions", json={"participant_code": p["code"], "block": 1}).json()
    assert session["mode"] == "study" and session["policy"] == block["policy"]
    assert session["explanation_mode"] == mode and session["seed"] == block["seed"]
    final = drive(client, session["id"])
    assert "summary" not in (final["outcome"] or {}), "participants do not see scored outcomes"
    for item in final["timeline"]:
        assert item["harm"] is None
        detail = item["decision_detail"]
        if detail is None:
            continue
        if mode in ("none", "placebo"):
            assert not detail["factors"] and detail["timing"] is None and not detail["reason_codes"]
        if mode == "factors":
            assert detail["timing"] is None
        if mode == "full" and detail["should_ask"]:
            assert detail["timing"] is not None
    events = client.get(f"/api/v1/session/{session['id']}/events").json()
    text = str(events)
    assert "'necessary'" not in text and "'error_present'" not in text


def test_instruments_and_scoring(client):
    instruments = {i["id"]: i for i in client.get("/api/v1/study/instruments").json()}
    assert instruments["nasa_tlx_raw"]["ready"] and instruments["agentpause_post_task"]["validated"] is False
    assert instruments["sus"]["ready"] is False and instruments["sus"]["redistributable"] is False
    p = enrol(client)
    tlx = {"mental": 50, "physical": 10, "temporal": 30, "performance": 20, "effort": 40, "frustration": 30}
    r = client.post(
        "/api/v1/study/responses",
        json={"participant_code": p["code"], "instrument_id": "nasa_tlx_raw", "responses": tlx},
    )
    assert r.status_code == 201 and r.json()["score"]["mean"] == pytest.approx(30.0)
    probe = {
        "control": 7,
        "timing": 6,
        "earlier_later": 2,
        "annoyance": 1,
        "understanding": 7,
        "trust": 5,
        "responsibility": 6,
    }
    score = client.post(
        "/api/v1/study/responses",
        json={"participant_code": p["code"], "instrument_id": "agentpause_post_task", "responses": probe},
    ).json()["score"]
    assert score["subscales"]["annoyance"] == 7  # reverse-coded: 1 → 7
    assert score["mean"] == pytest.approx((7 + 6 + 6 + 7 + 7 + 5 + 6) / 7)
    comp = client.post(
        "/api/v1/study/responses",
        json={
            "participant_code": p["code"],
            "instrument_id": "timing_comprehension",
            "responses": {"low_risk": "Continue without asking", "goal_questions": "None — it postpones everything"},
        },
    ).json()["score"]
    assert comp["correct"] == 1 and comp["answered"] == 2
    bad = client.post(
        "/api/v1/study/responses",
        json={"participant_code": p["code"], "instrument_id": "nasa_tlx_raw", "responses": {"mental": 500}},
    )
    assert bad.status_code == 422
    sus = client.post(
        "/api/v1/study/responses", json={"participant_code": p["code"], "instrument_id": "sus", "responses": {"q1": 3}}
    )
    assert sus.status_code == 409, "SUS items must be supplied locally first"
    unknown = client.post(
        "/api/v1/study/responses", json={"participant_code": p["code"], "instrument_id": "nope", "responses": {}}
    )
    assert unknown.status_code == 404


def test_local_instrument_items(tmp_path):
    import json

    from api_helpers import make_client

    items = [{"id": f"q{i}", "text": f"Item {i}"} for i in range(1, 11)]
    (tmp_path / "sus.json").write_text(json.dumps({"items": items}))
    with make_client(instruments_local_dir=str(tmp_path)) as c:
        sus = {i["id"]: i for i in c.get("/api/v1/study/instruments").json()}["sus"]
        assert sus["ready"] and sus["items_source"] == "local"
        p = enrol(c)
        answers = {f"q{i}": (5 if i % 2 else 1) for i in range(1, 11)}
        r = c.post(
            "/api/v1/study/responses",
            json={"participant_code": p["code"], "instrument_id": "sus", "responses": answers},
        )
        assert r.json()["score"]["sus"] == pytest.approx(100.0)


def test_config_update_and_export(secured):
    auth = {"Authorization": "Bearer s3cret"}
    config = secured.get("/api/v1/study/config").json()
    config["conditions"] = ["always_confirm", "adaptive"]
    assert secured.put("/api/v1/study/config", json=config).status_code == 401
    assert secured.put("/api/v1/study/config", json=config, headers=auth).status_code == 200
    p = secured.post("/api/v1/study/participants").json()
    assert len(p["plan"]) == 3
    bad = {**config, "conditions": ["telepathy"]}
    assert secured.put("/api/v1/study/config", json=bad, headers=auth).status_code == 422
    secured.patch(f"/api/v1/study/participants/{p['code']}", json={"consented": True})
    secured.post(
        "/api/v1/study/responses",
        json={"participant_code": p["code"], "instrument_id": "nasa_tlx_raw", "responses": {"mental": 10}},
    )
    assert secured.get("/api/v1/study/export").status_code == 401
    csv_text = secured.get("/api/v1/study/export", headers=auth).text
    assert csv_text.startswith("participant_code,participant_number,explanation_mode")
    assert p["code"] in csv_text
