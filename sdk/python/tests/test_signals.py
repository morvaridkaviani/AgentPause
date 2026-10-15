import pytest

from agentpause import ActionContext, Assumption, ConsequenceCategory, Provenance, SessionState
from agentpause.categories import CATEGORY_PRIORS, parse_category
from agentpause.model import ModelParameters
from agentpause.signals import DEFAULT_AGENT_CONFIDENCE, resolve_signals
from agentpause.state import ActionStats

P = ModelParameters()


def test_missing_signals_use_category_priors_and_are_flagged():
    ctx = ActionContext(action="send_email", category=ConsequenceCategory.EXTERNAL_COMMUNICATION)
    s = resolve_signals(ctx, SessionState(), P)
    prior = CATEGORY_PRIORS[ConsequenceCategory.EXTERNAL_COMMUNICATION]
    assert s.severity == prior.severity
    assert s.recoverability == prior.recoverability
    assert s.agent_confidence == DEFAULT_AGENT_CONFIDENCE
    assert s.provenance["severity"] == Provenance.DEFAULT
    assert {"severity", "recoverability", "agent_confidence", "intent_confidence"} <= set(s.missing)
    assert s.external_effects is True


def test_provided_signals_keep_provenance():
    ctx = ActionContext(
        action="x",
        severity=0.4,
        agent_confidence=0.9,
        cognitive_load=0.7,
        provenance={"cognitive_load": Provenance.SIMULATED},
    )
    s = resolve_signals(ctx, SessionState(), P)
    assert s.provenance["severity"] == Provenance.AGENT_PROVIDED
    assert s.provenance["cognitive_load"] == Provenance.SIMULATED
    assert "severity" not in s.missing


def test_out_of_range_values_are_clamped_with_warning():
    s = resolve_signals(ActionContext(action="x", agent_confidence=1.7, severity=-0.5), SessionState(), P)
    assert s.agent_confidence == 1.0
    assert s.severity == 0.0
    assert len(s.warnings) == 2


@pytest.mark.parametrize("reversible,rec", [(True, 0.1), (False, 0.9)])
def test_contradictory_reversibility_is_flagged_and_explicit_number_wins(reversible, rec):
    s = resolve_signals(ActionContext(action="x", reversible=reversible, recoverability=rec), SessionState(), P)
    assert s.recoverability == rec
    assert any(w.startswith("CONTRADICTORY_SIGNALS") for w in s.warnings)


def test_reversible_flag_maps_to_recoverability():
    s_rev = resolve_signals(
        ActionContext(action="x", category="external_communication", reversible=True), SessionState(), P
    )
    s_irr = resolve_signals(
        ActionContext(action="x", category="local_modification", reversible=False), SessionState(), P
    )
    assert s_rev.recoverability >= 0.9
    assert s_irr.recoverability <= 0.1


def test_assumptions_drive_intent_confidence():
    a = Assumption("date", "the date is Friday", 0.6)
    ctx = ActionContext(action="x", assumptions=(a,))
    s = resolve_signals(ctx, SessionState(), P)
    assert s.intent_confidence == pytest.approx(0.6)
    assert s.residual_intent_confidence == 1.0
    assert s.provenance["intent_confidence"] == Provenance.INFERRED


def test_resolved_assumptions_are_not_missing_intent():
    state = SessionState()
    state.assumptions["date"] = Assumption("date", "d", 0.6)
    state.resolve("date")
    s = resolve_signals(ActionContext(action="x", depends_on=("date",)), state, P)
    assert s.intent_confidence == 1.0
    assert "intent_confidence" not in s.missing


def test_undeclared_dependency_warns():
    s = resolve_signals(ActionContext(action="x", depends_on=("ghost",)), SessionState(), P)
    assert any("undeclared" in w for w in s.warnings)


def test_history_shrinks_intent_toward_observed_disagreement():
    state = SessionState()
    state.stats["send_email"] = ActionStats(approvals=0.0, disagreements=8.0, count=8)
    s = resolve_signals(ActionContext(action="send_email", intent_confidence=0.95), state, P)
    assert s.intent_confidence < 0.95
    assert s.history_disagreement_rate == 1.0
    approving = SessionState()
    approving.stats["send_email"] = ActionStats(approvals=8.0, disagreements=0.0, count=8)
    s2 = resolve_signals(ActionContext(action="send_email", intent_confidence=0.7), approving, P)
    assert s2.intent_confidence > 0.7


def test_breakpoint_inferred_at_task_start():
    s = resolve_signals(ActionContext(action="x", task_progress=0.0), SessionState(), P)
    assert s.at_breakpoint is True


@pytest.mark.parametrize(
    "value,expected",
    [
        ("external communication", ConsequenceCategory.EXTERNAL_COMMUNICATION),
        ("EXTERNAL-COMMUNICATION", ConsequenceCategory.EXTERNAL_COMMUNICATION),
        ("payment", ConsequenceCategory.FINANCIAL_TRANSACTION),
        ("delete_files", ConsequenceCategory.DATA_DELETION),
        ("something unheard of", ConsequenceCategory.OTHER),
        (None, ConsequenceCategory.OTHER),
    ],
)
def test_parse_category(value, expected):
    assert parse_category(value) == expected
