"""Enumerations shared across the AgentPause engine.

All enums are ``str`` subclasses so they serialize to readable JSON and compare equal to
their string values (``DecisionType.CONTINUE == "CONTINUE"``).
"""

from __future__ import annotations

from enum import StrEnum


class DecisionType(StrEnum):
    """What AgentPause tells the agent to do with a proposed action."""

    CONTINUE = "CONTINUE"
    """Execute the action without involving the human."""

    CLARIFY = "CLARIFY"
    """Before acting, ask the human a lightweight question about an intent assumption."""

    ASK_HUMAN = "ASK_HUMAN"
    """Before acting, ask the human to approve (or edit / reject) this specific action."""

    DEFER = "DEFER"
    """Execute this (reversible) action now; a question has been scheduled for a later,
    better moment, always before the first irreversible action that depends on it."""

    BLOCK = "BLOCK"
    """Do not execute. Hand control back to the human (hard constraint or unacceptable risk)."""

    @property
    def interrupts_now(self) -> bool:
        return self in (DecisionType.CLARIFY, DecisionType.ASK_HUMAN, DecisionType.BLOCK)

    @property
    def proceeds(self) -> bool:
        return self in (DecisionType.CONTINUE, DecisionType.DEFER)


class InterventionKind(StrEnum):
    """The form of the human-facing intervention recommended with a decision."""

    NONE = "none"
    CLARIFICATION = "clarification"  # choose / confirm an intent assumption
    CONFIRMATION = "confirmation"  # approve / edit / reject a concrete action
    BATCHED_REVIEW = "batched_review"  # several questions in one interruption
    TAKEOVER = "takeover"  # blocked: the human must decide or act themselves
    SCHEDULED = "scheduled"  # deferred: nothing shown now (an ambient notice at most)


class Provenance(StrEnum):
    """Where a signal value came from. Shown in the UI and logged with every decision.

    AgentPause does not pretend that every signal can be measured. Each value carries its
    provenance so that researchers and users can see what was measured and what was guessed.
    """

    AGENT_PROVIDED = "agent_provided"  # reported by the agent (e.g. its own confidence)
    USER_PROVIDED = "user_provided"  # stated by the user (preferences, explicit settings)
    ESTIMATED = "estimated"  # computed by a model or heuristic (e.g. a severity classifier)
    INFERRED = "inferred"  # derived from other signals or history inside AgentPause
    SIMULATED = "simulated"  # produced by the simulator (experiments and demos)
    DEFAULT = "default"  # nothing was provided; a documented category prior was used


class ConsequenceCategory(StrEnum):
    """Coarse category of an action's real-world consequence.

    Categories give default priors for severity and recoverability (see ``categories.py``).
    Callers should override the priors when they know better.
    """

    READ_ONLY = "read_only"
    INTERNAL_DRAFT = "internal_draft"
    LOCAL_MODIFICATION = "local_modification"
    DATA_ENTRY = "data_entry"
    EXTERNAL_COMMUNICATION = "external_communication"
    SCHEDULING = "scheduling"
    FINANCIAL_TRANSACTION = "financial_transaction"
    DATA_DELETION = "data_deletion"
    DATA_SHARING = "data_sharing"
    ACCOUNT_CHANGE = "account_change"
    OTHER = "other"


class AssumptionKind(StrEnum):
    """Type of missing information behind an intent assumption.

    Taxonomy follows Gulati et al. (2026), "Ask Early, Ask Late, Ask Right". They found
    that goal and constraint clarifications lose their value early in a trajectory, while
    input clarifications stay useful until about mid-trajectory. AgentPause therefore does
    not defer goal or constraint questions by default.
    """

    GOAL = "goal"
    CONSTRAINT = "constraint"
    INPUT = "input"
    CONTEXT = "context"


class ResponseType(StrEnum):
    """How the human responded to an intervention."""

    APPROVE = "approve"  # proceed as proposed
    EDIT = "edit"  # proceed with corrected parameters
    REJECT = "reject"  # do not execute this action; agent should propose an alternative
    ANSWER = "answer"  # answered a clarification question
    TAKEOVER = "takeover"  # human performs the step themselves (e.g. after BLOCK)
    OVERRIDE = "override"  # human overrides a BLOCK and allows the action
    CANCEL_TASK = "cancel_task"  # abandon the whole task
    ASK_WHY = "ask_why"  # requested an explanation (no state change)
    TIMEOUT = "timeout"  # no answer within the allowed time

    @property
    def disagrees_with_agent(self) -> bool:
        """True when the response indicates the agent's proposal was not what the user wanted."""
        return self in (ResponseType.EDIT, ResponseType.REJECT, ResponseType.TAKEOVER, ResponseType.CANCEL_TASK)

    @property
    def is_terminal(self) -> bool:
        """True when the response resolves the pending intervention."""
        return self not in (ResponseType.ASK_WHY,)


class Level(StrEnum):
    """Discretized level used in human-readable explanations."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
