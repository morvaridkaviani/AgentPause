import copy

import pytest

from agentpause_sim import ScenarioError, list_scenarios, load_scenario, parse_scenario

EXPECTED = ["travel", "email", "shopping", "files", "calendar", "research"]


def test_all_bundled_scenarios_load_in_order():
    assert [s.id for s in list_scenarios()] == EXPECTED


@pytest.mark.parametrize("sid", EXPECTED)
def test_scenario_structure(sid):
    sc = load_scenario(sid)
    assert sc.goal and sc.brief and sc.agent_name
    assert len(sc.steps) >= 7
    assert len(sc.assumptions) >= 3
    assert sc.mistakes, "every scenario needs injectable mistakes"
    assert any(not s.reversible for s in sc.steps), "every scenario has at least one irreversible step"
    assert any(s.breakpoint for s in sc.steps)
    for a in sc.assumptions:
        assert sc.dependents(a.id)
        assert sc.harm_step(a.id) >= sc.step_index(a.introduced_at)
    rendered = sc.render(sc.brief, {a.id: a.agent_value for a in sc.assumptions})
    assert "{" not in rendered, "brief placeholders must all be assumption ids"
    for step in sc.steps:
        text = sc.render(
            step.description + " ".join(step.preview.values()), {a.id: a.agent_value for a in sc.assumptions}
        )
        assert "{" not in text


def test_summary_and_dict_are_serializable():
    import json

    for sc in list_scenarios():
        json.dumps(sc.to_dict())
        assert sc.summary()["n_steps"] == len(sc.steps)


def _raw():
    return copy.deepcopy(
        {
            "id": "t",
            "assumptions": [
                {
                    "id": "a",
                    "description": "d",
                    "confidence": 0.7,
                    "agent_value": "x",
                    "alternatives": ["y"],
                    "introduced_at": "s1",
                }
            ],
            "steps": [
                {"id": "s1", "category": "read_only", "depends_on": ["a"]},
                {"id": "s2", "category": "financial_transaction", "depends_on": ["a"]},
            ],
            "mistakes": [{"id": "m", "step": "s1", "description": "oops", "probability": 0.1, "harm_at": "s2"}],
        }
    )


def test_minimal_scenario_parses_with_defaults():
    sc = parse_scenario(_raw())
    assert sc.assumptions[0].wrong_probability == pytest.approx(0.3)
    assert sc.mistakes[0].severity == sc.steps[1].severity
    assert sc.harm_step("a") == 1


@pytest.mark.parametrize(
    "mutate,match",
    [
        (lambda r: r.update(id=""), "needs an 'id'"),
        (lambda r: r.update(steps=[]), "no steps"),
        (lambda r: r["steps"][0].update(severity=2.0), "outside"),
        (lambda r: r["assumptions"][0].update(alternatives=[]), "alternative"),
        (lambda r: r["assumptions"][0].update(introduced_at="nowhere"), "not a step"),
        (lambda r: r["steps"][1].update(depends_on=["ghost"]), "unknown assumption"),
        (lambda r: r["mistakes"][0].update(harm_at="nowhere"), "unknown step"),
        (lambda r: r["steps"].append({"id": "s1"}), "duplicate"),
        (lambda r: r["steps"][1].update(skip_if={"a": "zzz"}), "not a known option"),
    ],
)
def test_invalid_scenarios_are_rejected(mutate, match):
    raw = _raw()
    mutate(raw)
    with pytest.raises(ScenarioError, match=match):
        parse_scenario(raw)


def test_unknown_scenario():
    with pytest.raises(KeyError):
        load_scenario("moon_landing")
