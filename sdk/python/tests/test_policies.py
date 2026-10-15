import copy

import pytest
from sdk_cases import low_risk, risky, timing_task

from agentpause import (
    ActionContext,
    AdaptivePolicy,
    Assumption,
    AssumptionKind,
    ConsequenceCategory,
    DecisionType,
    InterventionKind,
    ModelParameters,
    SessionState,
    UserPreferences,
    available_policies,
    create_policy,
)
from agentpause.explain.reasons import ReasonCode
from agentpause.policies import LearnedPolicy, register_policy
from agentpause.policies.base import InterventionPolicy

ALL = [
    "full_autonomy",
    "always_confirm",
    "fixed_threshold",
    "confidence_threshold",
    "rule_based",
    "myopic_voi",
    "adaptive",
    "user_customized",
    "learned",
]


# ---------------------------------------------------------------- registry & purity
def test_registry_lists_all_policies_with_metadata():
    names = {p["name"] for p in available_policies()}
    assert set(ALL) <= names
    core = {p["name"] for p in available_policies() if p.get("core")}
    assert core == {"full_autonomy", "always_confirm", "fixed_threshold", "adaptive"}


@pytest.mark.parametrize(
    "alias,name",
    [
        ("never", "full_autonomy"),
        ("ADAPTIVE-AGENTPAUSE", "adaptive"),
        ("threshold", "fixed_threshold"),
        ("voi", "myopic_voi"),
    ],
)
def test_aliases(alias, name):
    assert create_policy(alias).name == name


def test_unknown_policy_raises():
    with pytest.raises(ValueError, match="Unknown policy"):
        create_policy("telepathy")


@pytest.mark.parametrize("name", ALL)
@pytest.mark.parametrize("ctx_factory", [low_risk, risky])
def test_policies_are_pure_and_deterministic(name, ctx_factory):
    policy = create_policy(name)
    state = SessionState()
    state.interruption_steps = [0]
    before = copy.deepcopy(state.to_dict())
    ctx = ctx_factory(step=1)
    a = policy.decide(ctx, state)
    b = policy.decide(ctx, state)
    assert state.to_dict() == before, "decide() must not mutate the session state"
    assert a.to_dict() == b.to_dict()
    assert 0.0 <= a.score <= 1.0


@pytest.mark.parametrize("name", ALL)
def test_requires_human_input_blocks_for_every_policy(name):
    d = create_policy(name).decide(low_risk(requires_human_input=True), SessionState())
    assert d.decision == DecisionType.BLOCK
    assert d.recommended_intervention == InterventionKind.TAKEOVER
    assert ReasonCode.REQUIRES_HUMAN_INPUT.value in d.reason_codes


def test_register_custom_policy():
    class Coin(InterventionPolicy):
        name = "always_clarify_test"

        def decide(self, context, state):
            s = self.resolve(context, state)
            return self.make_decision(context, state, s, DecisionType.CLARIFY, score=0.9)

    register_policy("always_clarify_test", Coin)
    assert create_policy("always_clarify_test").decide(low_risk(), SessionState()).decision == DecisionType.CLARIFY


# ---------------------------------------------------------------- baselines
def test_full_autonomy_never_asks():
    assert create_policy("full_autonomy").decide(risky(), SessionState()).decision == DecisionType.CONTINUE


def test_always_confirm_skips_only_reads():
    policy = create_policy("always_confirm")
    assert policy.decide(low_risk(), SessionState()).decision == DecisionType.CONTINUE
    d = policy.decide(low_risk(category=ConsequenceCategory.INTERNAL_DRAFT), SessionState())
    assert d.decision == DecisionType.ASK_HUMAN
    everything = create_policy("always_confirm", include_read_only=True)
    assert everything.decide(low_risk(), SessionState()).decision == DecisionType.ASK_HUMAN


def test_fixed_threshold_ignores_uncertainty():
    policy = create_policy("fixed_threshold", threshold=0.35)
    confident = risky(agent_confidence=0.99, intent_confidence=0.99)
    assert policy.decide(confident, SessionState()).decision == DecisionType.ASK_HUMAN
    unsure_but_cheap = low_risk(agent_confidence=0.3, intent_confidence=0.3)
    assert policy.decide(unsure_but_cheap, SessionState()).decision == DecisionType.CONTINUE
    with pytest.raises(ValueError):
        create_policy("fixed_threshold", mode="vibes")


def test_confidence_threshold_ignores_stakes():
    policy = create_policy("confidence_threshold", threshold=0.8)
    assert policy.decide(low_risk(agent_confidence=0.5), SessionState()).decision == DecisionType.ASK_HUMAN
    assert (
        policy.decide(risky(agent_confidence=0.95, intent_confidence=0.95), SessionState()).decision
        == DecisionType.CONTINUE
    )
    a = Assumption("date", "the date is Friday", 0.5, options=("Fri", "Sat"), agent_value="Fri")
    d = policy.decide(low_risk(assumptions=(a,), intent_confidence=None), SessionState())
    assert d.decision == DecisionType.CLARIFY
    assert d.questions[0].assumption_id == "date"


def test_rule_based_rules():
    policy = create_policy("rule_based")
    assert policy.decide(low_risk(), SessionState()).decision == DecisionType.CONTINUE
    assert (
        policy.decide(risky(agent_confidence=0.99, intent_confidence=0.99), SessionState()).decision
        == DecisionType.ASK_HUMAN
    )
    reversible = ActionContext(
        action="move",
        category=ConsequenceCategory.LOCAL_MODIFICATION,
        recoverability=0.9,
        agent_confidence=0.95,
        intent_confidence=0.95,
    )
    assert policy.decide(reversible, SessionState()).decision == DecisionType.CONTINUE
    unsure = ActionContext(
        action="move",
        category=ConsequenceCategory.LOCAL_MODIFICATION,
        recoverability=0.9,
        agent_confidence=0.5,
        intent_confidence=0.95,
    )
    assert policy.decide(unsure, SessionState()).decision == DecisionType.ASK_HUMAN


# ---------------------------------------------------------------- adaptive: core behaviour
@pytest.fixture
def adaptive() -> AdaptivePolicy:
    return AdaptivePolicy()


def test_brief_example_asks_with_expected_reason_codes():
    d = create_policy("adaptive").decide(
        ActionContext.build(
            "send_email",
            consequence="external_communication",
            reversible=False,
            intent_confidence=0.72,
            agent_confidence=0.86,
            task_progress=0.91,
        ),
        SessionState(),
    )
    assert d.decision == DecisionType.ASK_HUMAN
    assert d.score > 0.5
    for code in ("LOW_INTENT_CONFIDENCE", "IRREVERSIBLE_ACTION", "EXTERNAL_CONSEQUENCE"):
        assert code in d.reason_codes
    assert d.recommended_intervention == InterventionKind.CONFIRMATION


def test_low_consequence_continues_even_when_uncertain(adaptive):
    d = adaptive.decide(low_risk(agent_confidence=0.5, intent_confidence=0.6), SessionState())
    assert d.decision == DecisionType.CONTINUE
    assert ReasonCode.ASKING_NOT_WORTH_IT.value in d.reason_codes


def test_high_consequence_and_uncertainty_asks(adaptive):
    d = adaptive.decide(risky(), SessionState())
    assert d.decision == DecisionType.ASK_HUMAN
    assert d.terms["value_action"] > 0


def test_high_reversibility_lowers_pressure(adaptive):
    irreversible = adaptive.decide(risky(), SessionState())
    reversible = adaptive.decide(risky(recoverability=0.95), SessionState())
    assert reversible.score < irreversible.score


def test_high_uncertainty_raises_pressure(adaptive):
    sure = adaptive.decide(risky(agent_confidence=0.98, intent_confidence=0.98), SessionState())
    unsure = adaptive.decide(risky(agent_confidence=0.5, intent_confidence=0.5), SessionState())
    assert unsure.score > sure.score


def test_catastrophic_actions_are_blocked(adaptive):
    d = adaptive.decide(
        risky(severity=0.95, recoverability=0.0, agent_confidence=0.3, intent_confidence=0.9), SessionState()
    )
    assert d.decision == DecisionType.BLOCK
    assert ReasonCode.CATASTROPHIC_RISK.value in d.reason_codes
    no_block = AdaptivePolicy(block_catastrophic=False)
    assert (
        no_block.decide(risky(severity=0.95, recoverability=0.0, agent_confidence=0.3), SessionState()).decision
        == DecisionType.ASK_HUMAN
    )


def test_missing_data_still_decides_and_flags(adaptive):
    d = adaptive.decide(ActionContext(action="mystery"), SessionState())
    assert d.decision in DecisionType
    assert ReasonCode.MISSING_SIGNAL_DEFAULTED.value in d.reason_codes


def test_contradictory_signals_flagged(adaptive):
    d = adaptive.decide(risky(reversible=True, recoverability=0.05), SessionState())
    assert ReasonCode.CONTRADICTORY_SIGNALS.value in d.reason_codes


def test_habituation_reduces_value_of_asking(adaptive):
    fresh = adaptive.decide(risky(step=10), SessionState())
    tired = SessionState(step=10)
    tired.interruption_steps = list(range(3, 10))
    habituated = adaptive.decide(risky(step=10), tired)
    assert habituated.terms["catch_probability"] < fresh.terms["catch_probability"]
    assert habituated.score < fresh.score


def test_load_and_breakpoints_raise_interruption_cost(adaptive):
    calm = adaptive.decide(risky(cognitive_load=0.0, at_breakpoint=True), SessionState())
    busy = adaptive.decide(risky(cognitive_load=1.0, at_breakpoint=False), SessionState())
    assert busy.terms["interruption_cost_now"] > calm.terms["interruption_cost_now"]


# ---------------------------------------------------------------- adaptive: timing
def test_deferrable_question_is_deferred_and_batched_before_commitment(adaptive):
    d = adaptive.decide(timing_task(1, introduce=True), SessionState(step=1))
    assert d.decision == DecisionType.DEFER
    assert len(d.deferred) == 1
    deferred = d.deferred[0]
    assert deferred.assumption_id == "seat"
    assert deferred.target_step in (2, 3)
    assert deferred.deadline_step == 3, "deadline is the first irreversible dependent step"
    assert deferred.target_step <= deferred.deadline_step
    assert ReasonCode.DEFERRED_TO_BREAKPOINT.value in d.reason_codes
    timing = next(t for t in d.item_timings if t.item_id == "assumption:seat")
    assert {c.step for c in timing.candidates} >= {1, deferred.target_step}
    assert max(c.step for c in timing.candidates) <= 3


def test_myopic_policy_asks_now_instead_of_deferring():
    d = create_policy("myopic_voi").decide(timing_task(1, introduce=True), SessionState(step=1))
    assert d.decision == DecisionType.CLARIFY
    assert not d.deferred


def test_goal_assumptions_are_never_deferred(adaptive):
    ctx = timing_task(1, introduce=True)
    goal = Assumption("seat", "you want an aisle seat", 0.75, AssumptionKind.GOAL, ("aisle", "window"), "aisle")
    from dataclasses import replace

    d = adaptive.decide(replace(ctx, assumptions=(goal,)), SessionState(step=1))
    assert d.decision == DecisionType.CLARIFY
    timing = next(t for t in d.item_timings if t.item_id == "assumption:seat")
    assert not timing.deferrable


def test_deferred_question_is_asked_by_its_deadline():
    from agentpause import AgentPause

    pause = AgentPause("adaptive")
    first = pause.evaluate(context=timing_task(1, introduce=True))
    assert first.decision == DecisionType.DEFER
    asked_at = None
    for step in (2, 3):
        d = pause.evaluate(context=timing_task(step))
        if d.should_ask:
            asked_at = step
            assert any(q.assumption_id == "seat" for q in d.questions)
            break
    assert asked_at is not None and asked_at <= 3


def test_interrupting_anyway_piggybacks_other_questions(adaptive):
    a1 = Assumption("date", "the date is Friday", 0.6, AssumptionKind.INPUT, ("Fri", "Sat"), "Fri")
    a2 = Assumption("budget", "budget covers both", 0.8, AssumptionKind.CONSTRAINT, ("both", "flight only"), "both")
    ctx = risky(assumptions=(a1, a2), intent_confidence=None, agent_confidence=0.6)
    d = adaptive.decide(ctx, SessionState())
    assert d.decision == DecisionType.ASK_HUMAN
    assert len(d.questions) >= 2
    assert d.recommended_intervention == InterventionKind.BATCHED_REVIEW
    assert sum(1 for q in d.questions if not q.piggybacked) == 1


# ---------------------------------------------------------------- user preferences
def _borderline():
    return ActionContext.build(
        "send_email",
        consequence="external_communication",
        reversible=False,
        intent_confidence=0.95,
        agent_confidence=0.95,
    )


def test_preference_profile_changes_decision():
    balanced = create_policy("adaptive").decide(_borderline(), SessionState())
    fewer = create_policy("adaptive", preferences={"profile": "fewer_interruptions"}).decide(
        _borderline(), SessionState()
    )
    assert balanced.decision == DecisionType.ASK_HUMAN
    assert fewer.decision == DecisionType.CONTINUE
    local = ActionContext(
        action="rename", category=ConsequenceCategory.LOCAL_MODIFICATION, agent_confidence=0.8, intent_confidence=1.0
    )
    assert create_policy("adaptive").decide(local, SessionState()).decision == DecisionType.CONTINUE
    assert (
        create_policy("adaptive", preferences={"profile": "maximum_control"}).decide(local, SessionState()).decision
        == DecisionType.ASK_HUMAN
    )


def test_unknown_profile_rejected():
    with pytest.raises(ValueError):
        UserPreferences.from_dict({"profile": "yolo"})


def test_user_rules():
    always = create_policy("user_customized", preferences={"always_ask_categories": ["read_only"]})
    d = always.decide(low_risk(), SessionState())
    assert d.decision == DecisionType.ASK_HUMAN and ReasonCode.USER_RULE_ALWAYS_ASK.value in d.reason_codes
    never = create_policy("user_customized", preferences={"never_ask_categories": ["financial_transaction"]})
    d = never.decide(risky(), SessionState())
    assert d.decision == DecisionType.CONTINUE and ReasonCode.USER_RULE_NEVER_ASK.value in d.reason_codes
    block = create_policy("user_customized", preferences={"block_categories": ["data_deletion"]})
    assert (
        block.decide(low_risk(category=ConsequenceCategory.DATA_DELETION), SessionState()).decision
        == DecisionType.BLOCK
    )
    irreversible = create_policy("user_customized", preferences={"ask_before_irreversible": True})
    confident = risky(agent_confidence=0.99, intent_confidence=0.99, cognitive_load=1.0)
    d = irreversible.decide(confident, SessionState())
    assert d.decision == DecisionType.ASK_HUMAN and ReasonCode.USER_RULE_IRREVERSIBLE.value in d.reason_codes
    external = create_policy("user_customized", preferences={"ask_before_external": True})
    assert external.decide(_borderline(), SessionState()).decision == DecisionType.ASK_HUMAN


def test_low_risk_autonomy_and_budget():
    allow = create_policy(
        "user_customized", preferences={"allow_low_risk_autonomy": True, "profile": "maximum_control"}
    )
    local = ActionContext(
        action="rename", category=ConsequenceCategory.LOCAL_MODIFICATION, agent_confidence=0.8, intent_confidence=1.0
    )
    d = allow.decide(local, SessionState())
    assert d.decision == DecisionType.CONTINUE and ReasonCode.USER_RULE_LOW_RISK_AUTONOMY.value in d.reason_codes
    budget = create_policy("user_customized", preferences={"max_interruptions_per_task": 2})
    exhausted = SessionState(step=5)
    exhausted.interruption_steps = [1, 2]
    d = budget.decide(risky(step=5), exhausted)
    assert d.decision == DecisionType.CONTINUE and ReasonCode.INTERRUPTION_BUDGET_EXHAUSTED.value in d.reason_codes


def test_user_block_beats_never_ask():
    prefs = {"never_ask_categories": ["data_deletion"], "block_categories": ["data_deletion"]}
    d = create_policy("user_customized", preferences=prefs).decide(
        low_risk(category=ConsequenceCategory.DATA_DELETION), SessionState()
    )
    assert d.decision == DecisionType.BLOCK


# ---------------------------------------------------------------- learned (experimental)
def test_learned_policy_loads_bundled_weights():
    policy = create_policy("learned")
    assert isinstance(policy, LearnedPolicy)
    d = policy.decide(risky(), SessionState())
    assert 0.0 <= d.terms["p_intervention_needed"] <= 1.0
    assert (
        policy.decide(risky(agent_confidence=0.3), SessionState()).score
        >= policy.decide(low_risk(), SessionState()).score
    )


def test_learned_policy_missing_weights(tmp_path):
    with pytest.raises(FileNotFoundError):
        LearnedPolicy(weights_path=str(tmp_path / "nope.json"))


def test_custom_parameters_are_used():
    cheap = create_policy("adaptive", parameters={"interruption_cost": 0.0001})
    assert (
        cheap.decide(
            low_risk(category=ConsequenceCategory.LOCAL_MODIFICATION, agent_confidence=0.9), SessionState()
        ).decision
        == DecisionType.ASK_HUMAN
    )
    expensive = create_policy("adaptive", parameters=ModelParameters(interruption_cost=10.0, block_severity=1.1))
    assert expensive.decide(risky(), SessionState()).decision == DecisionType.CONTINUE
