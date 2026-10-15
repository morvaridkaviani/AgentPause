"""Natural-language explanations built from reason codes (deterministic templates, no LLM).

Templates keep explanations reproducible and *faithful*: every clause maps to a reason code
that the policy actually emitted. Post-hoc LLM rationalizations can sound convincing while
being wrong (Ehsan & Riedl 2021), and placebic reasons can raise trust as much as real ones
(Eiband et al. 2019). AgentPause therefore never generates explanation text with a model.
"""

from __future__ import annotations

from ..context import ActionContext
from ..decision import Decision
from ..state import SessionState
from ..types import DecisionType
from .reasons import DATA_QUALITY_CODES, ReasonCode, phrase

# Codes that describe circumstances rather than reasons, shown in a second sentence.
_CONTEXT_CODES = {ReasonCode.AT_BREAKPOINT.value, ReasonCode.BATCHED_QUESTIONS.value}


def _join(parts: list[str]) -> str:
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " and " + parts[-1]


def _main_reasons(decision: Decision, limit: int = 3) -> list[str]:
    skip = {d.value for d in DATA_QUALITY_CODES} | _CONTEXT_CODES
    return [phrase(code) for code in decision.reason_codes if code not in skip][:limit]


def build_explanation(decision: Decision, context: ActionContext, state: SessionState) -> str:
    reasons = _main_reasons(decision)
    sentences: list[str] = []
    kind = decision.decision

    if kind == DecisionType.ASK_HUMAN:
        sentences.append(
            f"AgentPause asked for your confirmation because {_join(reasons) or 'the policy requires it'}."
        )
    elif kind == DecisionType.CLARIFY:
        question = next((q for q in decision.questions if q.assumption_id), None)
        assumption = None
        if question and question.assumption_id:
            assumption = next(
                (a for a in context.assumptions if a.id == question.assumption_id), None
            ) or state.assumptions.get(question.assumption_id)
        if assumption is not None:
            stakes = ""
            if ReasonCode.COMMITMENT_POINT.value in decision.reason_codes:
                stakes = ", and the next action depends on it and cannot be undone"
            elif ReasonCode.DEPENDENT_COMMITMENT.value in decision.reason_codes:
                stakes = ", and a later step that cannot be undone depends on it"
            sentences.append(
                f"AgentPause asked a quick question because the agent had to guess that "
                f"{assumption.description} ({assumption.confidence:.0%} sure){stakes}."
            )
        else:
            sentences.append(f"AgentPause asked a clarifying question because {_join(reasons)}.")
    elif kind == DecisionType.DEFER:
        deferred = decision.deferred[0] if decision.deferred else None
        if deferred is not None:
            target = (deferred.target_action or "").replace("_", " ")
            sentences.append(
                f"AgentPause let the agent continue with this step, which can be undone, and will ask about "
                f"“{deferred.description}” at step {deferred.target_step + 1} ('{target}') instead of interrupting you now."
            )
        else:
            sentences.append("AgentPause let the agent continue and postponed a question to a better moment.")
    elif kind == DecisionType.BLOCK:
        sentences.append(f"AgentPause stopped the agent because {_join(reasons) or 'the action is not allowed'}.")
    else:
        sentences.append(
            f"AgentPause let the agent continue because {_join(reasons) or 'nothing required your input'}."
        )

    if ReasonCode.BATCHED_QUESTIONS.value in decision.reason_codes and decision.questions:
        sentences.append(f"It combined {len(decision.questions)} questions into this one interruption.")
    if decision.signals.get("missing"):
        missing = ", ".join(str(m).replace("_", " ") for m in decision.signals["missing"])
        sentences.append(f"Note: some information was not provided ({missing}), so documented defaults were used.")
    if any(str(w).startswith("CONTRADICTORY_SIGNALS") for w in decision.warnings):
        sentences.append("Note: some of the information provided was contradictory; see the warnings.")
    return " ".join(sentences)
