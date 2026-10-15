"""A parametric simulated user for automated experiments.

SIMULATION ASSUMPTIONS (documented in research/metrics.md):

* When asked about a *visible* problem, the user catches it with a probability that drops
  with habituation. This is the rubber-stamping effect reported in the warning and consent
  literature (Böhme & Köpsell 2010; Akhawe & Felt 2013; Anderson et al. 2015) and for agent
  approvals (Anthropic 2026: 93% of prompts approved).
* Clarification questions ("Is X right?") are assumed easier to answer correctly than
  spotting an error inside an approval card.
* The user's habituation parameters may be set *differently* from those the adaptive policy
  assumes. That makes it possible to test robustness under model misspecification
  (``experiments/configs/sensitivity.toml``).

The simulated user is a modelling device for comparing policies under stated assumptions.
It does **not** stand in for human-participant data.
"""

from __future__ import annotations

import math
import random
from dataclasses import asdict, dataclass, field, fields, replace
from typing import Any

from agentpause import DecisionType, ResponseType


@dataclass(frozen=True)
class SimulatedUserParams:
    approval_vigilance: float = 0.85
    """P(catch a visible mistake in an approval card) when not habituated."""
    clarification_accuracy: float = 0.95
    """P(correctly answering a clarification about a wrong assumption) when not habituated."""
    habituation_rate: float = 0.12
    habituation_effect: float = 0.5
    habituation_window: int = 8
    false_reject_rate: float = 0.03
    """P(rejecting a correct action)."""
    block_override_rate: float = 0.7
    """When a correct action is blocked: P(override) vs. taking over manually."""
    base_response_s: float = 4.0
    per_question_s: float = 2.5
    load_response_s: float = 4.0
    edit_s: float = 10.0
    takeover_s: float = 45.0
    response_noise: float = 0.25

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> SimulatedUserParams:
        if not data:
            return cls()
        known = {f.name for f in fields(cls)}
        unknown = set(data) - known
        if unknown:
            raise ValueError(f"Unknown simulated-user parameter(s): {sorted(unknown)}")
        return replace(cls(), **data)


@dataclass
class CardTruth:
    """What the simulator knows about an intervention card: the ground truth the user may or may not notice."""

    step_index: int
    decision: DecisionType
    load: float
    has_confirmation: bool
    requires_human_input: bool
    action_mistakes: list[str] = field(default_factory=list)
    assumptions: dict[str, tuple[str, str]] = field(default_factory=dict)
    """assumption id → (value shown by the agent, the user's true value)."""
    recent_interruptions: int = 0
    n_questions: int = 1


@dataclass
class HumanResponse:
    """A human's (real or simulated) response to an intervention card."""

    response: ResponseType
    answers: dict[str, str] = field(default_factory=dict)
    response_time_s: float = 0.0
    source: str = "simulated"

    def to_dict(self) -> dict[str, Any]:
        return {
            "response": self.response.value,
            "answers": dict(self.answers),
            "response_time_s": round(self.response_time_s, 3),
            "source": self.source,
        }


class SimulatedUser:
    def __init__(self, params: SimulatedUserParams | None = None) -> None:
        self.params = params or SimulatedUserParams()

    def habituation(self, recent_interruptions: int) -> float:
        return 1.0 - math.exp(-self.params.habituation_rate * max(0, recent_interruptions))

    def respond(self, truth: CardTruth, rng: random.Random) -> HumanResponse:
        p = self.params
        h = self.habituation(truth.recent_interruptions)
        attention = 1.0 - p.habituation_effect * h

        answers: dict[str, str] = {}
        for a_id, (shown, true_value) in truth.assumptions.items():
            if shown != true_value and rng.random() < p.clarification_accuracy * attention:
                answers[a_id] = true_value
            else:
                answers[a_id] = shown  # confirmed (correctly, or rubber-stamped)

        extra = 0.0
        if truth.decision == DecisionType.BLOCK:
            wrong = bool(truth.action_mistakes) or any(s != t for s, t in truth.assumptions.values())
            if truth.requires_human_input or wrong or rng.random() >= p.block_override_rate:
                response = ResponseType.TAKEOVER
                extra = p.takeover_s
            else:
                response = ResponseType.OVERRIDE
        elif truth.has_confirmation:
            if truth.action_mistakes and rng.random() < p.approval_vigilance * attention:
                response = ResponseType.EDIT
                extra = p.edit_s
            elif not truth.action_mistakes and rng.random() < p.false_reject_rate:
                response = ResponseType.REJECT
            else:
                response = ResponseType.APPROVE
        else:
            response = ResponseType.ANSWER

        base = p.base_response_s + p.per_question_s * max(1, truth.n_questions) + p.load_response_s * truth.load
        noise = math.exp(rng.gauss(0.0, p.response_noise)) if p.response_noise > 0 else 1.0
        return HumanResponse(response=response, answers=answers, response_time_s=base * noise + extra)
