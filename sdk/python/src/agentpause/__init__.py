"""AgentPause: adaptive human intervention timing for AI agents.

Quick start::

    from agentpause import AgentPause

    pause = AgentPause(policy="adaptive")
    decision = pause.evaluate(
        action="send_email",
        consequence="external_communication",
        reversible=False,
        intent_confidence=0.72,
        agent_confidence=0.86,
    )
    if decision.should_ask:
        print(decision.explanation)
"""

from .categories import CATEGORY_PRIORS, parse_category
from .client import AgentPauseAPIError, AgentPauseClient
from .context import ActionContext, Assumption, PlannedAction, UserPreferences
from .decision import (
    Counterfactual,
    Decision,
    DeferredQuestion,
    Factor,
    ItemTiming,
    Question,
    TimingCandidate,
    TimingExplanation,
    TimingNote,
)
from .explain import Explainer, ReasonCode
from .model import ModelParameters
from .policies import (
    AdaptivePolicy,
    AlwaysConfirmPolicy,
    ConfidenceThresholdPolicy,
    FullAutonomyPolicy,
    InterventionPolicy,
    LearnedPolicy,
    MyopicVOIPolicy,
    RuleBasedPolicy,
    ThresholdPolicy,
    UserCustomizedPolicy,
    available_policies,
    create_policy,
    register_policy,
)
from .session import AgentPause
from .signals import ResolvedSignals, resolve_signals
from .state import SessionState
from .types import (
    AssumptionKind,
    ConsequenceCategory,
    DecisionType,
    InterventionKind,
    Level,
    Provenance,
    ResponseType,
)

__version__ = "0.1.0"

__all__ = [
    "CATEGORY_PRIORS",
    "ActionContext",
    "AdaptivePolicy",
    "AgentPause",
    "AgentPauseAPIError",
    "AgentPauseClient",
    "AlwaysConfirmPolicy",
    "Assumption",
    "AssumptionKind",
    "ConfidenceThresholdPolicy",
    "ConsequenceCategory",
    "Counterfactual",
    "Decision",
    "DecisionType",
    "DeferredQuestion",
    "Explainer",
    "Factor",
    "FullAutonomyPolicy",
    "InterventionKind",
    "InterventionPolicy",
    "ItemTiming",
    "LearnedPolicy",
    "Level",
    "ModelParameters",
    "MyopicVOIPolicy",
    "PlannedAction",
    "Provenance",
    "Question",
    "ReasonCode",
    "ResolvedSignals",
    "ResponseType",
    "RuleBasedPolicy",
    "SessionState",
    "ThresholdPolicy",
    "TimingCandidate",
    "TimingExplanation",
    "TimingNote",
    "UserCustomizedPolicy",
    "UserPreferences",
    "__version__",
    "available_policies",
    "create_policy",
    "parse_category",
    "register_policy",
    "resolve_signals",
]
