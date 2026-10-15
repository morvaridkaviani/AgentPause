import itertools
import math

import pytest

from agentpause.model import (
    ModelParameters,
    catch_probability,
    clamp01,
    error_cost,
    error_probability,
    habituation,
    interruption_cost,
    is_commitment,
    rework_cost,
    score_from_terms,
)
from agentpause.types import AssumptionKind, InterventionKind

P = ModelParameters()


def test_error_probability_combines_independent_sources():
    assert error_probability(1.0, 1.0) == 0.0
    assert error_probability(0.0, 1.0) == 1.0
    assert error_probability(0.9, 0.8) == pytest.approx(1 - 0.72)


def test_error_probability_clamps_out_of_range_inputs():
    assert error_probability(1.5, -0.2) == 1.0


def test_error_cost_is_severity_for_irreversible_and_small_for_recoverable():
    assert error_cost(0.8, 0.0, P) == pytest.approx(0.8)
    recoverable = error_cost(0.8, 1.0, P)
    assert recoverable == pytest.approx(0.8 * P.undo_cost_fraction)
    assert recoverable < error_cost(0.8, 0.5, P) < error_cost(0.8, 0.0, P)


def test_habituation_is_monotone_and_saturating():
    values = [habituation(n, P) for n in range(30)]
    assert values[0] == 0.0
    assert all(b > a for a, b in itertools.pairwise(values))
    assert values[-1] < 1.0


def test_catch_probability_drops_with_habituation():
    assert catch_probability(0.0, P) == pytest.approx(P.base_catch_probability)
    assert catch_probability(1.0, P) == pytest.approx(P.base_catch_probability * (1 - P.habituation_effect))


@pytest.mark.parametrize("load_a,load_b", [(0.0, 0.5), (0.5, 1.0)])
def test_interruption_cost_grows_with_load(load_a, load_b):
    kw = {"at_breakpoint": True, "habituation_level": 0.0, "kind": InterventionKind.CONFIRMATION, "params": P}
    assert interruption_cost(cognitive_load=load_a, **kw) < interruption_cost(cognitive_load=load_b, **kw)


def test_interruption_cost_breakpoints_and_kinds():
    kw = {"cognitive_load": 0.3, "habituation_level": 0.0, "params": P}
    at_bp = interruption_cost(at_breakpoint=True, kind=InterventionKind.CONFIRMATION, **kw)
    mid = interruption_cost(at_breakpoint=False, kind=InterventionKind.CONFIRMATION, **kw)
    unknown = interruption_cost(at_breakpoint=None, kind=InterventionKind.CONFIRMATION, **kw)
    assert at_bp < unknown < mid
    clarify = interruption_cost(at_breakpoint=True, kind=InterventionKind.CLARIFICATION, **kw)
    assert clarify == pytest.approx(at_bp * P.clarification_cost_multiplier)


def test_preference_multiplier_scales_cost():
    kw = {
        "cognitive_load": 0.3,
        "at_breakpoint": True,
        "habituation_level": 0.0,
        "kind": InterventionKind.CONFIRMATION,
        "params": P,
    }
    assert interruption_cost(preference_multiplier=2.5, **kw) == pytest.approx(2.5 * interruption_cost(**kw))


def test_score_boundary_is_net_value_sign():
    assert score_from_terms(0.2, 0.1) > 0.5
    assert score_from_terms(0.1, 0.2) < 0.5
    assert score_from_terms(0.0, 0.0) == 0.0


def test_commitment_and_rework():
    assert is_commitment(0.1, P)
    assert not is_commitment(0.9, P)
    assert rework_cost(0.5, P) > rework_cost(0.0, P) > 0


def test_clamp_handles_nan():
    assert clamp01(math.nan) == 0.0


def test_parameters_roundtrip_and_unknown_keys():
    params = ModelParameters(interruption_cost=0.05)
    data = params.to_dict()
    assert sorted(data["deferrable_kinds"]) == ["context", "input"]
    restored = ModelParameters.from_dict(data)
    assert restored == params
    assert AssumptionKind.INPUT in restored.deferrable_kinds
    with pytest.raises(ValueError):
        ModelParameters.from_dict({"not_a_parameter": 1})
