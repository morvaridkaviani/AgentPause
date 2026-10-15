import pytest
from sdk_cases import low_risk, risky, timing_task

from agentpause import AgentPause, DecisionType, Explainer, create_policy
from agentpause.explain.reasons import PHRASES, ReasonCode, phrase


def test_every_reason_code_has_a_phrase():
    assert set(PHRASES) == set(ReasonCode)
    assert phrase("NOT_A_CODE") == "not a code"


def test_ask_explanation_names_the_reasons():
    d = AgentPause().evaluate(
        "send_email",
        consequence="external_communication",
        reversible=False,
        intent_confidence=0.72,
        agent_confidence=0.86,
    )
    assert d.explanation.startswith("AgentPause asked for your confirmation because")
    assert "difficult to undo" in d.explanation
    assert "did not clearly specify" in d.explanation
    assert "defaults were used" in d.explanation  # severity etc. were not provided


def test_factors_report_level_provenance_and_direction():
    d = AgentPause().evaluate(context=risky())
    by_signal = {f.signal: f for f in d.factors}
    assert {"agent_confidence", "severity", "recoverability", "cognitive_load"} <= set(by_signal)
    assert by_signal["recoverability"].display == "hard to undo"
    assert by_signal["recoverability"].contribution > 0, "irreversibility pushes toward asking"
    assert by_signal["severity"].provenance.value == "agent_provided"
    top = d.top_factors(2)
    assert all(f.contribution > 0 for f in top)


def test_feature_counterfactuals_are_faithful():
    """Applying a counterfactual must actually produce the stated alternative decision."""
    pause = AgentPause()
    ctx = risky()
    d = pause.evaluate(context=ctx, record=False)
    features = [c for c in d.counterfactuals if c.kind == "feature"]
    assert features, "a risky ASK should have at least one counterfactual"
    for cf in features:
        assert cf.counterfactual_decision != d.decision
        altered = ctx.with_signal(cf.signal, cf.counterfactual_value)
        if cf.signal == "recoverability":
            from dataclasses import replace

            altered = replace(altered, reversible=None)
        assert pause.policy.decide(altered, pause.state).decision == cf.counterfactual_decision
        assert cf.text.startswith("If ")


def test_timing_explanation_for_action_approval():
    d = AgentPause().evaluate(context=risky())
    assert "Approval only makes sense before an action runs" in d.timing.why_now
    assert "cannot be undone" in d.timing.why_not_later
    assert d.timing.why_not_earlier == "This is the first step of the task."


def test_timing_explanation_for_defer_and_later_ask():
    pause = AgentPause("adaptive")
    d = pause.evaluate(context=timing_task(1, introduce=True))
    assert d.decision == DecisionType.DEFER
    assert "did not interrupt you now" in d.timing.why_now
    assert "will not wait past step 4" in d.timing.why_not_later  # step index 3 shown 1-indexed
    assert d.timing.later, "later candidate moments are listed"
    asked = None
    for step in (2, 3):
        decision = pause.evaluate(context=timing_task(step))
        if decision.should_ask:
            asked = decision
            break
    assert asked is not None
    assert "postponed" in asked.timing.why_not_earlier
    assert any("scheduled this question" in note.text for note in asked.timing.earlier)


def test_timing_explanation_for_myopic_policy_is_honest():
    pause = AgentPause("myopic_voi")
    d = pause.evaluate(context=timing_task(1, introduce=True))
    assert d.decision == DecisionType.CLARIFY
    assert "became unsure about this at this step" in d.timing.why_now


def test_baseline_policies_say_they_do_not_plan():
    pause = AgentPause("confidence_threshold")
    pause.evaluate(context=low_risk(step=0))
    d = pause.evaluate(context=low_risk(step=1, agent_confidence=0.4))
    assert d.decision == DecisionType.ASK_HUMAN
    later_text = d.timing.why_not_later
    assert "would already have run" in later_text


def test_continue_timing_mentions_costs():
    d = AgentPause().evaluate(context=low_risk())
    assert d.decision == DecisionType.CONTINUE
    assert "Nothing at this step was worth interrupting you for" in d.timing.why_now


def test_stability_is_a_probability_and_lower_near_the_boundary():
    pause = AgentPause()
    clear = pause.evaluate(context=low_risk(), record=False)
    assert clear.confidence == pytest.approx(1.0)
    borderline = pause.evaluate(
        "send_email",
        consequence="external_communication",
        reversible=False,
        intent_confidence=0.95,
        agent_confidence=0.95,
        record=False,
    )
    assert 0.0 <= borderline.confidence <= 1.0
    assert borderline.confidence < 1.0


@pytest.mark.parametrize("level", ["none", "light", "full"])
def test_explain_levels(level):
    d = AgentPause(explain=level).evaluate(context=risky())
    if level == "none":
        assert d.explanation == "" and not d.factors and d.timing is None
    elif level == "light":
        assert d.explanation and not d.factors and d.timing is None
    else:
        assert d.explanation and d.factors and d.timing is not None and d.confidence is not None


def test_invalid_explain_level():
    with pytest.raises(ValueError):
        Explainer("verbose")


def test_explanations_work_for_every_policy():
    for name in [
        "full_autonomy",
        "always_confirm",
        "fixed_threshold",
        "confidence_threshold",
        "rule_based",
        "myopic_voi",
        "adaptive",
        "user_customized",
        "learned",
    ]:
        pause = AgentPause(create_policy(name))
        d = pause.evaluate(context=risky())
        assert d.explanation
        assert d.timing is not None and d.timing.why_now
