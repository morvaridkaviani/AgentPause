"""Counterfactual *timing* explanations: "Why now?", "Why not earlier?", "Why not later?".

The explanations are faithful by construction:

* **Earlier**: read from the session history. Each earlier step stores what the policy
  actually computed there: the value of asking each open question, whether a question was
  scheduled for later, and the decision and score. Nothing is re-imagined after the fact.
* **Later**: computed from the same policy evaluation at the planned future steps (candidate
  moments, their interruption cost, rework, and the commitment-point deadline). For policies
  that do not plan (all baselines), the text says so instead of inventing a reason.

Prior art for the question form: Krarup et al. (JAIR 2021) contrastive "why at time T rather
than earlier/later" questions for planners (FQ7), and Fox, Long & Magazzeni (2017).
AgentPause applies the form to an agent's decisions to involve a human.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..context import ActionContext, Assumption
from ..decision import Decision, ItemTiming, TimingExplanation, TimingNote
from ..state import HistoryEntry, SessionState
from ..types import AssumptionKind, DecisionType
from .reasons import DATA_QUALITY_CODES, ReasonCode, phrase

if TYPE_CHECKING:
    from ..policies.base import InterventionPolicy


def _humanize(action: str) -> str:
    return action.replace("_", " ")


def _at(step: int, action: str) -> str:
    """User-facing step label (1-indexed)."""
    return f"step {step + 1} ('{_humanize(action)}')"


def _undo_phrase(recoverability: float) -> str:
    if recoverability >= 0.8:
        return "it could be undone afterwards, at a small cost"
    if recoverability >= 0.4:
        return "it could only partly be undone"
    return "it cannot be undone"


def _cost_reason(entry: HistoryEntry) -> str:
    signals = entry.signals
    if signals.get("at_breakpoint") is False:
        return "you were in the middle of a sub-task, so interrupting would have cost more"
    if float(signals.get("cognitive_load", 0.0)) >= 0.6:
        return "you appeared busy, so interrupting would have cost more"
    return "the expected harm it could prevent was smaller than the cost of interrupting you"


def _find_assumption(assumption_id: str, context: ActionContext, state: SessionState) -> Assumption | None:
    for assumption in context.assumptions:
        if assumption.id == assumption_id:
            return assumption
    return state.assumptions.get(assumption_id)


def _timing_for(decision: Decision, item_id: str) -> ItemTiming | None:
    return next((t for t in decision.item_timings if t.item_id == item_id), None)


def explain_timing(
    decision: Decision,
    context: ActionContext,
    state: SessionState,
    policy: InterventionPolicy | None = None,
) -> TimingExplanation:
    """Build the timing explanation. ``state`` must be the state *before* this decision was recorded."""
    history = [h for h in state.history if h.step < decision.step]
    plans = bool(decision.item_timings)
    policy_name = policy.name if policy is not None else decision.policy

    if decision.decision in (DecisionType.ASK_HUMAN, DecisionType.CLARIFY):
        primary = next((q for q in decision.questions if not q.piggybacked), None) or (
            decision.questions[0] if decision.questions else None
        )
        if primary is not None and primary.assumption_id:
            return _explain_assumption_question(
                decision, context, state, history, primary.assumption_id, plans, policy_name
            )
        return _explain_action_question(decision, context, history, plans, policy_name)
    if decision.decision == DecisionType.DEFER and decision.deferred:
        return _explain_defer(decision, state)
    if decision.decision == DecisionType.BLOCK:
        return _explain_block(decision, context)
    return _explain_continue(decision, context, history, plans, policy_name)


# --------------------------------------------------------------------------------------
def _explain_assumption_question(
    decision: Decision,
    context: ActionContext,
    state: SessionState,
    history: list[HistoryEntry],
    assumption_id: str,
    plans: bool,
    policy_name: str,
) -> TimingExplanation:
    item_id = f"assumption:{assumption_id}"
    timing = _timing_for(decision, item_id)
    assumption = _find_assumption(assumption_id, context, state)
    description = assumption.description if assumption else assumption_id
    introduced = state.assumption_introduced.get(assumption_id, decision.step)
    step = decision.step

    # ---- why now
    now_parts: list[str] = []
    if introduced == step:
        now_parts.append(f"The agent became unsure about this at this step ({description}).")
    if timing is not None and timing.commitment_step is not None:
        if timing.commitment_step == step:
            now_parts.append(
                "The current action depends on it and cannot be undone, so this is the last moment to check."
            )
        else:
            now_parts.append(
                f"A later step, '{_humanize(timing.commitment_action or '')}', depends on it and cannot be undone."
            )
    later_candidates = [c for c in (timing.candidates if timing else []) if c.step > step]
    if timing is not None and timing.deferrable and later_candidates:
        best_later = max(later_candidates, key=lambda c: c.value)
        now_value = timing.candidates[0].value
        if best_later.rework_cost > 0 and best_later.value < now_value:
            now_parts.append(
                f"Waiting until {_at(best_later.step, best_later.action)} would risk redoing work if the guess is wrong, "
                "so asking now is worth more."
            )
        elif best_later.value < now_value:
            now_parts.append(
                f"Later moments, such as {_at(best_later.step, best_later.action)}, would be more disruptive."
            )
    elif (
        timing is not None
        and assumption is not None
        and assumption.kind in (AssumptionKind.GOAL, AssumptionKind.CONSTRAINT)
    ):
        now_parts.append(
            "Questions about your goals and constraints lose their value quickly once work starts, so they are asked right away."
        )
    if decision.signals.get("at_breakpoint"):
        now_parts.append("You are also at a natural pause in the task.")
    if not now_parts:
        now_parts.append(_policy_reason(decision))
    why_now = " ".join(now_parts)

    # ---- why not earlier
    relevant = [h for h in history if h.step >= introduced]
    earlier_notes: list[TimingNote] = []
    for entry in relevant[-4:]:
        target = entry.deferred_targets.get(assumption_id)
        value = entry.item_values.get(item_id)
        if target is not None:
            text = f"At {_at(entry.step, entry.action)}, AgentPause scheduled this question for step {target + 1} instead of interrupting you."
        elif value is not None and value <= 0:
            text = f"At {_at(entry.step, entry.action)}, asking was not yet worth it: {_cost_reason(entry)}."
        elif value is not None:
            text = f"At {_at(entry.step, entry.action)}, asking was considered (net value {value:+.3f}) but a later moment looked better."
        else:
            text = f"At {_at(entry.step, entry.action)}, the {policy_name} policy decided {entry.decision.value} (score {entry.score:.2f})."
        earlier_notes.append(TimingNote(entry.step, entry.action, text, entry.decision, value))
    if introduced >= step or not relevant:
        why_not_earlier = "There was no earlier moment: the agent only became unsure about this at this step."
    elif any(entry.deferred_targets.get(assumption_id) is not None for entry in relevant):
        why_not_earlier = (
            "AgentPause deliberately postponed this question to avoid interrupting you mid-task; "
            "this is the moment it had planned."
        )
    elif plans:
        why_not_earlier = "Earlier, asking would have cost you more than it could prevent at that point."
    else:
        why_not_earlier = (
            f"The {policy_name} policy only asks once its own rule is triggered, which happened at this step."
        )

    # ---- why not later
    later_notes = [
        TimingNote(
            c.step, c.action, f"Asking at {_at(c.step, c.action)}: net value {c.value:+.3f} ({c.note}).", value=c.value
        )
        for c in later_candidates
    ]
    if timing is not None and timing.commitment_step == step:
        why_not_later = "There is no later moment: once this step runs, it cannot be undone."
    elif timing is not None and timing.deferrable and later_candidates:
        why_not_later = (
            f"AgentPause compared {len(later_candidates)} later moment(s); none was better than now "
            f"(the best later option was {max(c.value for c in later_candidates):+.3f} vs {timing.candidates[0].value:+.3f} now)."
        )
    elif timing is not None and not timing.deferrable:
        why_not_later = (
            "AgentPause does not postpone questions about goals or constraints: evidence suggests they lose "
            "most of their value early in a task (Gulati et al. 2026)."
            if assumption is not None and assumption.kind in (AssumptionKind.GOAL, AssumptionKind.CONSTRAINT)
            else "There is no later breakpoint before the step that depends on this."
        )
    else:
        why_not_later = f"The {policy_name} policy decides one step at a time and does not plan when to ask."
    return TimingExplanation(why_now, why_not_earlier, why_not_later, earlier_notes, later_notes)


def _explain_action_question(
    decision: Decision, context: ActionContext, history: list[HistoryEntry], plans: bool, policy_name: str
) -> TimingExplanation:
    action = _humanize(context.action)
    why_now = f"Approval only makes sense before an action runs, and this is the step where '{action}' would run. {_policy_reason(decision)}"
    earlier_notes = [
        TimingNote(
            h.step,
            h.action,
            f"At {_at(h.step, h.action)}: {h.decision.value} (score {h.score:.2f}).",
            h.decision,
            h.score,
        )
        for h in history[-4:]
    ]
    if not history:
        why_not_earlier = "This is the first step of the task."
    else:
        highest = max(h.score for h in history)
        why_not_earlier = (
            f"This action was first proposed at this step. The earlier steps carried less risk "
            f"(highest earlier score {highest:.2f} vs {decision.score:.2f} now)."
        )
    recoverability = float(decision.signals.get("recoverability", 0.5))
    why_not_later = f"If AgentPause waited, '{action}' would already have run without your review, and {_undo_phrase(recoverability)}."
    return TimingExplanation(why_now.strip(), why_not_earlier, why_not_later, earlier_notes, [])


def _explain_defer(decision: Decision, state: SessionState) -> TimingExplanation:
    deferred = decision.deferred[0]
    reasons = []
    if decision.signals.get("at_breakpoint") is False:
        reasons.append("you are in the middle of a sub-task")
    if float(decision.signals.get("cognitive_load", 0.0)) >= 0.6:
        reasons.append("you appear busy")
    timing = _timing_for(decision, f"assumption:{deferred.assumption_id}")
    target = next((c for c in (timing.candidates if timing else []) if c.step == deferred.target_step), None)
    if target is not None and target.batched:
        reasons.append("the question can be combined with another interruption that is expected anyway")
    if not reasons:
        reasons.append("a later moment is less disruptive")
    target_label = _at(deferred.target_step, deferred.target_action or "")
    deadline = (
        f", before '{_humanize(deferred.deadline_action)}', which cannot be undone" if deferred.deadline_action else ""
    )
    why_now = (
        f"AgentPause did not interrupt you now because this step can be undone and {' and '.join(reasons)}. "
        f"It will ask about “{deferred.description}” at {target_label}{deadline}."
    )
    introduced = state.assumption_introduced.get(deferred.assumption_id, decision.step)
    why_not_earlier = (
        "The question only came up at this step."
        if introduced >= decision.step
        else "Earlier steps did not depend on the answer in a way that made asking worthwhile."
    )
    later_notes = [
        TimingNote(
            c.step, c.action, f"Asking at {_at(c.step, c.action)}: net value {c.value:+.3f} ({c.note}).", value=c.value
        )
        for c in (timing.candidates if timing else [])
        if c.step > decision.step
    ]
    if deferred.deadline_step is not None and deferred.deadline_action:
        why_not_later = (
            f"AgentPause will not wait past {_at(deferred.deadline_step, deferred.deadline_action)}: after that step runs, "
            "your answer could no longer prevent a mistake."
        )
    else:
        why_not_later = "AgentPause will ask before the last step that depends on the answer."
    return TimingExplanation(why_now, why_not_earlier, why_not_later, [], later_notes)


def _explain_block(decision: Decision, context: ActionContext) -> TimingExplanation:
    if ReasonCode.REQUIRES_HUMAN_INPUT.value in decision.reason_codes:
        why_now = "The agent cannot complete this step without something only you can provide."
        why_not_later = "The task cannot continue past this step without you."
    else:
        why_now = f"AgentPause stopped '{_humanize(context.action)}' because {_policy_reason(decision, lowercase=True)}"
        why_not_later = "Waiting would not make the action safe: it would run without your review and cannot be undone."
    return TimingExplanation(why_now, "The action was first proposed at this step.", why_not_later)


def _explain_continue(
    decision: Decision, context: ActionContext, history: list[HistoryEntry], plans: bool, policy_name: str
) -> TimingExplanation:
    terms = decision.terms
    if plans and "benefit_action" in terms:
        why_now = (
            "Nothing at this step was worth interrupting you for: a question could prevent an expected harm of "
            f"{terms['benefit_action']:.3f}, while interrupting would cost {terms['interruption_cost_now']:.3f}."
        )
    else:
        why_now = f"Nothing at this step met the {policy_name} policy's criteria for asking. {_policy_reason(decision)}"
    interrupted = [h for h in history if h.interrupted]
    why_not_earlier = (
        f"You were last consulted at {_at(interrupted[-1].step, interrupted[-1].action)}."
        if interrupted
        else "No earlier step required your input."
    )
    why_not_later = (
        "AgentPause re-evaluates before every step and will ask before any step that cannot be undone if it is worth it."
        if plans
        else f"The {policy_name} policy re-evaluates each step independently."
    )
    return TimingExplanation(why_now.strip(), why_not_earlier, why_not_later)


def _policy_reason(decision: Decision, *, lowercase: bool = False) -> str:
    codes = [c for c in decision.reason_codes if c not in {d.value for d in DATA_QUALITY_CODES}]
    if not codes:
        return ""
    text = phrase(codes[0])
    if lowercase:
        return text + "."
    return text[0].upper() + text[1:] + "."
