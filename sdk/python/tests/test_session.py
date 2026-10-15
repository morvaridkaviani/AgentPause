import json

import pytest
from sdk_cases import low_risk, risky, timing_task

from agentpause import (
    ActionContext,
    AgentPause,
    Decision,
    DecisionType,
    ResponseType,
    SessionState,
)
from agentpause.integrations import ActionBlocked, ActionRejected, InterventionRequired


def test_readme_example():
    pause = AgentPause(policy="adaptive")
    decision = pause.evaluate(
        action="send_email",
        consequence="external_communication",
        reversible=False,
        intent_confidence=0.72,
        agent_confidence=0.86,
    )
    assert decision.should_ask
    assert not decision.should_proceed
    payload = decision.to_dict()
    assert payload["decision"] == "ASK_HUMAN"
    assert json.dumps(payload)  # JSON-serializable


def test_evaluate_requires_action_or_context():
    with pytest.raises(TypeError):
        AgentPause().evaluate()
    with pytest.raises(TypeError):
        AgentPause().evaluate(context=low_risk(), severity=0.1)


def test_evaluate_accepts_aliases_and_extra_metadata():
    d = AgentPause().evaluate("x", user_intent_confidence=0.5, consequence="payment", ticket_id="T-1")
    assert d.signals["intent_confidence"] == pytest.approx(0.5)
    ctx = ActionContext.build("x", ticket_id="T-1")
    assert ctx.metadata == {"ticket_id": "T-1"}


def test_record_false_does_not_change_state():
    pause = AgentPause()
    pause.evaluate(context=risky(), record=False)
    assert pause.state.step == 0 and not pause.state.history


def test_history_and_steps_advance():
    pause = AgentPause()
    pause.evaluate(context=low_risk())
    d = pause.evaluate(context=risky())
    assert pause.state.step == 2
    assert len(pause.state.history) == 2
    assert pause.state.interruption_steps == [d.step]


def test_responses_update_history_and_change_later_decisions():
    pause = AgentPause()
    ctx = ActionContext.build(
        "send_email",
        consequence="external_communication",
        reversible=False,
        intent_confidence=0.9,
        agent_confidence=0.95,
    )
    first = pause.evaluate(context=ctx)
    for _ in range(6):
        d = pause.evaluate(context=ctx)
        if d.should_ask:
            pause.respond(d, ResponseType.REJECT)
    stats = pause.state.stats["send_email"]
    assert stats.disagreements >= 1
    assert pause.evaluate(context=ctx, record=False).score >= first.score


def test_rubber_stamped_approvals_count_less():
    pause = AgentPause()
    d = pause.evaluate(context=risky())
    pause.state.history[-1].habituation = 0.8
    pause.respond(d, ResponseType.APPROVE)
    assert pause.state.stats["purchase_ticket"].approvals == pytest.approx(1 - 0.5 * 0.8)


def test_clarification_answers_resolve_assumptions():
    pause = AgentPause("myopic_voi")
    d = pause.evaluate(context=timing_task(1, introduce=True))
    assert d.decision == DecisionType.CLARIFY
    pause.respond(d, "answer", answers={"seat": "window"})
    assert pause.state.resolved["seat"] == "corrected"
    assert not pause.pending_questions


def test_declare_assumption_and_plan_api():
    pause = AgentPause()
    pause.declare_assumption("date", "the date is Friday", 0.6, kind="input", options=["Fri", "Sat"], agent_value="Fri")
    pause.set_plan([{"step": 2, "action": "purchase", "category": "financial_transaction", "depends_on": ["date"]}])
    assert pause.state.assumptions["date"].confidence == 0.6
    assert pause.state.plan[0].step == 2
    pause.resolve_assumption("date", correct=False)
    assert pause.state.resolved["date"] == "corrected"


@pytest.mark.parametrize("policy", ["adaptive", "myopic_voi", "user_customized", "fixed_threshold", "learned"])
def test_serialization_roundtrip_reproduces_decisions(policy):
    pause = AgentPause(policy, preferences={"profile": "maximum_control"} if policy == "user_customized" else None)
    pause.evaluate(context=timing_task(1, introduce=True))
    restored = AgentPause.from_dict(json.loads(json.dumps(pause.to_dict())))
    assert restored.policy.name == pause.policy.name
    nxt = timing_task(2)
    assert (
        restored.evaluate(context=nxt, record=False).to_dict()["decision"]
        == pause.evaluate(context=nxt, record=False).to_dict()["decision"]
    )


def test_decision_and_state_dict_roundtrip():
    pause = AgentPause()
    d = pause.evaluate(context=timing_task(1, introduce=True))
    again = Decision.from_dict(json.loads(json.dumps(d.to_dict())))
    assert again.to_dict() == d.to_dict()
    state = SessionState.from_dict(json.loads(json.dumps(pause.state.to_dict())))
    assert state.to_dict() == pause.state.to_dict()


def test_explain_timing_after_the_fact():
    pause = AgentPause(explain="light")
    d = pause.evaluate(context=risky())
    timing = pause.explain_timing(d)
    assert timing.why_now


# ---------------------------------------------------------------- guard decorator
def test_guard_runs_low_risk_tools():
    pause = AgentPause()
    calls = []

    @pause.guard(signals={"consequence": "read_only", "agent_confidence": 0.95})
    def search(q):
        calls.append(q)
        return f"results for {q}"

    assert search("flights") == "results for flights"
    assert calls == ["flights"]


def test_guard_asks_and_respects_answer():
    pause = AgentPause()
    signals = {
        "consequence": "external_communication",
        "reversible": False,
        "intent_confidence": 0.7,
        "agent_confidence": 0.8,
    }

    @pause.guard(signals=signals, on_ask=lambda d: True)
    def send(to):
        return f"sent to {to}"

    assert send("prof@example.org") == "sent to prof@example.org"

    @pause.guard(action="send_again", signals=signals, on_ask=lambda d: "reject")
    def send_again(to):
        return "should not run"

    with pytest.raises(ActionRejected):
        send_again("x")

    @pause.guard(action="send_unhandled", signals=signals)
    def send_unhandled(to):
        return "should not run"

    with pytest.raises(InterventionRequired) as err:
        send_unhandled("x")
    assert err.value.decision.should_ask


def test_guard_blocks():
    pause = AgentPause()

    @pause.guard(
        signals={
            "consequence": "financial_transaction",
            "severity": 0.95,
            "recoverability": 0.0,
            "agent_confidence": 0.2,
        }
    )
    def wire_money():
        return "sent"

    with pytest.raises(ActionBlocked):
        wire_money()


def test_guard_context_fn_supplies_dynamic_signals():
    pause = AgentPause()
    seen = {}

    def ctx(amount):
        seen["amount"] = amount
        return {
            "consequence": "payment",
            "severity": min(1.0, amount / 1000),
            "agent_confidence": 0.99,
            "intent_confidence": 0.99,
        }

    @pause.guard(context_fn=ctx, on_ask=lambda d: True)
    def pay(amount):
        return amount

    assert pay(5) == 5
    assert seen["amount"] == 5
    assert pause.decisions[-1].decision == DecisionType.CONTINUE


def test_labelled_policy_survives_a_round_trip():
    """Experiments and the API rename policies with display labels; sessions must still restore."""
    pause = AgentPause("adaptive", parameters={"interruption_cost": 0.03})
    pause.policy.name = "adaptive@0.03"
    pause.evaluate("send_email", consequence="external_communication", reversible=False)
    restored = AgentPause.from_dict(json.loads(json.dumps(pause.to_dict())))
    assert restored.policy.name == "adaptive@0.03"
    assert restored.policy.registry_key == "adaptive"
    assert restored.policy.parameters.interruption_cost == 0.03
    assert len(restored.state.history) == 1


def test_learned_policy_keeps_its_weights_path(tmp_path):
    from agentpause.policies.learned import DEFAULT_WEIGHTS_PATH

    weights = tmp_path / "weights.json"
    weights.write_text(DEFAULT_WEIGHTS_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    pause = AgentPause("learned", weights_path=str(weights))
    restored = AgentPause.from_dict(json.loads(json.dumps(pause.to_dict())))
    assert restored.policy.weights_path == str(weights)


def test_dataclasses_accept_plain_strings():
    from agentpause.context import ActionContext, Assumption, PlannedAction
    from agentpause.types import AssumptionKind, ConsequenceCategory, Provenance

    assumption = Assumption("dates", "'next Friday' means 14 Nov", 0.6, kind="input", options=["14 Nov", "21 Nov"])
    step = PlannedAction(step=1, action="buy", category="financial_transaction", reversible=False, depends_on=["dates"])
    ctx = ActionContext(
        "search",
        category="read_only",
        assumptions=[assumption],
        plan=[step],
        step=0,
        depends_on=["dates"],
        provenance={"agent_confidence": "estimated"},
    )
    assert assumption.kind is AssumptionKind.INPUT and assumption.options == ("14 Nov", "21 Nov")
    assert step.category is ConsequenceCategory.FINANCIAL_TRANSACTION
    assert ctx.category is ConsequenceCategory.READ_ONLY and isinstance(ctx.plan, tuple)
    assert ctx.provenance["agent_confidence"] is Provenance.ESTIMATED
    assert AgentPause("adaptive").evaluate(ctx).decision.value in {"CONTINUE", "DEFER", "CLARIFY"}
