"""Trajectory-aware adaptive intervention policy (the AgentPause model).

How it decides, per proposed action at step ``i``:

1. **Hard constraints.** BLOCK if the step needs the human, or if the action is catastrophic:
   high severity, irreversible, and probably wrong.
2. **Approval question** for the action itself. Its value is
   ``V_act = p_act · C_err · e − C_int(i)``, where ``p_act`` uses the agent's confidence and any
   *residual* intent ambiguity not attached to an explicit assumption. Its deadline is now:
   once the action runs, approval is moot.
3. **Clarification questions**, one per unresolved assumption that the current action or a
   planned action depends on. Each assumption has a **commitment point**: the first dependent
   action that is hard to undo. Asking after that point cannot prevent the harm, so the
   question's deadline is the commitment point. For each candidate moment ``t`` (now, later
   natural breakpoints, and the deadline itself) the value is::

       V(a, t) = p_wrong(a) · C_err(commitment) · e − C_int(t) − RW(a, i→t)

   ``RW`` is the expected rework of dependent reversible steps executed before ``t``.
   ``C_int(t)`` is discounted when another question is already scheduled at ``t`` (batching).
   Only *deferrable* assumption kinds (input, context) get later candidates. Goal and
   constraint questions lose their value early (Gulati et al. 2026).
4. **Assembly.**
   - If any question's best moment is *now* and its value is positive, interrupt now.
   - When interrupting, other questions are **piggybacked** if their marginal value now
     (cost × ``batch_marginal_cost``) is positive and at least their value at their own best
     moment.
   - If the interruption includes the action approval, the result is ASK_HUMAN; otherwise
     CLARIFY.
   - If nothing is worth asking now but some question is worth asking later, the result is
     DEFER: the current reversible action proceeds, and the question is scheduled.
   - Otherwise CONTINUE.

With ``timing=False`` the policy becomes the *myopic* expected-value baseline (``myopic_voi``).
It only asks "is asking worth it right now?". That ablation isolates the contribution of
re-timing and batching (hypothesis H1b).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ..categories import prior_for
from ..context import ActionContext, Assumption, PlannedAction, UserPreferences
from ..decision import Decision, DeferredQuestion, ItemTiming, Question, TimingCandidate
from ..explain.reasons import ReasonCode
from ..model import (
    ModelParameters,
    catch_probability,
    clamp01,
    error_cost,
    error_probability,
    interruption_cost,
    is_commitment,
    rework_cost,
    score_from_terms,
)
from ..signals import IRREVERSIBLE_MAX_RECOVERABILITY, REVERSIBLE_MIN_RECOVERABILITY, ResolvedSignals
from ..state import SessionState
from ..types import DecisionType, InterventionKind
from .base import (
    InterventionPolicy,
    action_question,
    assumption_question,
    autonomy_reasons,
    consequence_reasons,
    uncertainty_reasons,
)


@dataclass(frozen=True)
class _Dependent:
    step: int
    action: str
    severity: float
    recoverability: float
    at_breakpoint: bool | None
    cognitive_load: float | None
    is_current: bool


def _planned_signals(planned: PlannedAction) -> tuple[float, float]:
    prior = prior_for(planned.category)
    severity = planned.severity if planned.severity is not None else prior.severity
    if planned.recoverability is not None:
        recoverability = planned.recoverability
    elif planned.reversible is True:
        recoverability = max(prior.recoverability, REVERSIBLE_MIN_RECOVERABILITY)
    elif planned.reversible is False:
        recoverability = min(prior.recoverability, IRREVERSIBLE_MAX_RECOVERABILITY)
    else:
        recoverability = prior.recoverability
    return clamp01(severity), clamp01(recoverability)


class AdaptivePolicy(InterventionPolicy):
    name = "adaptive"
    summary = (
        "Weighs the expected harm a question can prevent against the cost of interrupting, and "
        "chooses the best moment to ask (now, at a later breakpoint, or never)."
    )

    def __init__(
        self,
        parameters: ModelParameters | None = None,
        preferences: UserPreferences | None = None,
        *,
        timing: bool = True,
        block_catastrophic: bool = True,
        name: str | None = None,
    ) -> None:
        super().__init__(parameters, preferences)
        self.timing = timing
        self.block_catastrophic = block_catastrophic
        if name:
            self.name = name
        elif not timing:
            self.name = "myopic_voi"

    def config(self) -> dict[str, Any]:
        return {"timing": self.timing, "block_catastrophic": self.block_catastrophic}

    @property
    def preference_multiplier(self) -> float:
        return self.preferences.interruption_cost_multiplier if self.preferences else 1.0

    # ------------------------------------------------------------------------------------
    def decide(self, context: ActionContext, state: SessionState) -> Decision:
        signals = self.resolve(context, state)
        hard = self.hard_constraint(context, state, signals)
        if hard is not None:
            return hard
        if self.block_catastrophic and self.is_catastrophic(signals):
            return self.catastrophic_block(context, state, signals)

        p = self.parameters
        step = self.step_of(context, state)
        plan = sorted(context.plan or state.plan, key=lambda pa: pa.step)
        future = [pa for pa in plan if pa.step > step]
        e_now = catch_probability(signals.habituation, p)

        def cint(load: float, at_breakpoint: bool | None, kind: InterventionKind) -> float:
            return interruption_cost(
                cognitive_load=load,
                at_breakpoint=at_breakpoint,
                habituation_level=signals.habituation,
                kind=kind,
                params=p,
                preference_multiplier=self.preference_multiplier,
            )

        # --- 1. approval of the current action ---------------------------------------
        p_act = error_probability(signals.agent_confidence, signals.residual_intent_confidence)
        c_act = error_cost(signals.severity, signals.recoverability, p)
        b_act = p_act * c_act * e_now
        cost_act = cint(signals.cognitive_load, signals.at_breakpoint, InterventionKind.CONFIRMATION)
        act_candidate = TimingCandidate(
            step=step,
            action=context.action,
            feasible=True,
            benefit=b_act,
            interruption_cost=cost_act,
            rework_cost=0.0,
            at_breakpoint=signals.at_breakpoint,
            note="approval of this action (only possible before it runs)",
        )
        act_timing = ItemTiming(
            item_id="action",
            label=context.description or context.action,
            is_assumption=False,
            deferrable=False,
            commitment_step=step,
            commitment_action=context.action,
            candidates=[act_candidate],
            chosen_step=step if act_candidate.value > 0 else None,
        )

        # Planned steps that will probably need a confirmation anyway. A deferred question
        # can ride along with such a confirmation at marginal cost (batching).
        anticipated = self._anticipated_confirmations(future, signals) if self.timing else set()

        # --- 2. clarification questions for unresolved assumptions --------------------
        known: dict[str, Assumption] = dict(state.assumptions)
        for assumption in context.assumptions:
            known[assumption.id] = assumption
        current_deps = set(context.dependency_ids)
        assumption_items: list[tuple[Assumption, ItemTiming]] = []
        for assumption in known.values():
            if assumption.id in state.resolved:
                continue
            dependents: list[_Dependent] = []
            if assumption.id in current_deps:
                dependents.append(
                    _Dependent(
                        step,
                        context.action,
                        signals.severity,
                        signals.recoverability,
                        signals.at_breakpoint,
                        signals.cognitive_load,
                        True,
                    )
                )
            for planned in future:
                if assumption.id in planned.depends_on:
                    sev, rec = _planned_signals(planned)
                    dependents.append(
                        _Dependent(
                            planned.step, planned.action, sev, rec, planned.at_breakpoint, planned.cognitive_load, False
                        )
                    )
            if not dependents:
                continue
            timing = self._assumption_timing(
                assumption, dependents, step, context, future, signals, e_now, cint, state, anticipated
            )
            assumption_items.append((assumption, timing))

        # --- 3. assemble ----------------------------------------------------------------
        questions: list[Question] = []
        triggered: list[tuple[str, float]] = []  # (item id, value now at full cost)
        if act_timing.chosen_step == step:
            triggered.append(("action", act_candidate.value))
        for _, timing in assumption_items:
            if timing.chosen_step == step:
                now = timing.candidates[0]
                triggered.append((timing.item_id, now.value))
        triggered.sort(key=lambda item: -item[1])
        interrupting = bool(triggered)

        deferred: list[DeferredQuestion] = []
        if interrupting:
            primary = triggered[0][0]
            included: set[str] = set()
            # approval item
            if act_timing.chosen_step == step:
                full = primary == "action"
                cost = cost_act if full else cost_act * p.batch_marginal_cost
                questions.append(action_question(context, benefit=b_act, cost=cost, piggybacked=not full))
                included.add("action")
            elif b_act - cost_act * p.batch_marginal_cost > 0:
                questions.append(
                    action_question(context, benefit=b_act, cost=cost_act * p.batch_marginal_cost, piggybacked=True)
                )
                included.add("action")
            # assumption items
            for assumption, timing in assumption_items:
                now = timing.candidates[0]
                if timing.chosen_step == step:
                    full = primary == timing.item_id
                    cost = now.interruption_cost if full else now.interruption_cost * p.batch_marginal_cost
                    questions.append(
                        assumption_question(assumption, benefit=now.benefit, cost=cost, piggybacked=not full)
                    )
                    included.add(timing.item_id)
                    continue
                marginal_value = now.benefit - now.interruption_cost * p.batch_marginal_cost
                later_value = timing.best.value if timing.best and timing.chosen_step is not None else 0.0
                if marginal_value > 0 and marginal_value >= later_value:
                    questions.append(
                        assumption_question(
                            assumption,
                            benefit=now.benefit,
                            cost=now.interruption_cost * p.batch_marginal_cost,
                            piggybacked=True,
                        )
                    )
                    included.add(timing.item_id)

        for assumption, timing in assumption_items:
            if timing.item_id in {f"assumption:{q.assumption_id}" for q in questions if q.assumption_id}:
                continue
            if timing.chosen_step is not None and timing.chosen_step > step:
                best = timing.best
                target = next((c for c in timing.candidates if c.step == timing.chosen_step), best)
                deferred.append(
                    DeferredQuestion(
                        assumption_id=assumption.id,
                        description=assumption.description,
                        kind=assumption.kind,
                        created_step=state.assumption_introduced.get(assumption.id, step),
                        target_step=timing.chosen_step,
                        target_action=target.action if target else None,
                        deadline_step=timing.commitment_step
                        if timing.commitment_step is not None
                        else max(c.step for c in timing.candidates),
                        deadline_action=timing.commitment_action,
                        value_now=timing.candidates[0].value,
                        value_at_target=target.value if target else 0.0,
                    )
                )

        # --- 4. decision type, score, reasons ---------------------------------------------
        scores = [score_from_terms(b_act, cost_act)] + [
            score_from_terms(t.candidates[0].benefit, t.candidates[0].interruption_cost) for _, t in assumption_items
        ]
        score = max(scores)
        terms = self._terms(signals, p_act, c_act, e_now, cost_act, b_act, assumption_items)

        if questions:
            has_confirmation = any(q.kind == InterventionKind.CONFIRMATION for q in questions)
            decision_type = DecisionType.ASK_HUMAN if has_confirmation else DecisionType.CLARIFY
            reasons = self._ask_reasons(context, signals, questions, assumption_items, step, has_confirmation)
            decision = self.make_decision(
                context, state, signals, decision_type, score=score, reasons=reasons, questions=questions, terms=terms
            )
        elif deferred:
            reasons = [ReasonCode.DEFERRED_TO_BREAKPOINT]
            if signals.recoverability >= 0.5:
                reasons.append(ReasonCode.REVERSIBLE_ACTION)
            if signals.at_breakpoint is False:
                reasons.append(ReasonCode.MID_TASK)
            if signals.cognitive_load >= 0.6:
                reasons.append(ReasonCode.HIGH_COGNITIVE_LOAD)
            if any(any(c.batched for c in t.candidates if c.step == t.chosen_step) for _, t in assumption_items):
                reasons.append(ReasonCode.BATCHED_QUESTIONS)
            decision = self.make_decision(
                context, state, signals, DecisionType.DEFER, score=score, reasons=reasons, terms=terms
            )
        else:
            reasons = [ReasonCode.ASKING_NOT_WORTH_IT, *autonomy_reasons(context, signals, p)]
            if signals.cognitive_load >= 0.6:
                reasons.append(ReasonCode.HIGH_COGNITIVE_LOAD)
            if signals.habituation >= 0.3 and self._worth_it_without_habituation(signals, p_act, c_act):
                reasons.append(ReasonCode.HABITUATION_RISK)
            decision = self.make_decision(
                context, state, signals, DecisionType.CONTINUE, score=score, reasons=reasons, terms=terms
            )

        decision.deferred = deferred
        decision.item_timings = [act_timing] + [t for _, t in assumption_items]
        return decision

    # ------------------------------------------------------------------------------------
    def _assumption_timing(
        self,
        assumption: Assumption,
        dependents: list[_Dependent],
        step: int,
        context: ActionContext,
        future: list[PlannedAction],
        signals: ResolvedSignals,
        e_now: float,
        cint: Callable[[float, bool | None, InterventionKind], float],
        state: SessionState,
        anticipated: set[int],
    ) -> ItemTiming:
        p = self.parameters
        commitment = next((d for d in dependents if is_commitment(d.recoverability, p)), None)
        if commitment is not None:
            harm = error_cost(commitment.severity, commitment.recoverability, p)
            deadline = commitment.step
        else:
            harm = max(error_cost(d.severity, d.recoverability, p) for d in dependents)
            deadline = max(d.step for d in dependents)
        p_wrong = clamp01(1.0 - assumption.confidence)
        deferrable = self.timing and assumption.kind in p.deferrable_kinds and deadline > step

        slots: list[tuple[int, str, float, bool | None]] = [
            (step, context.action, signals.cognitive_load, signals.at_breakpoint)
        ]
        if deferrable:
            for planned in future:
                if planned.step > deadline:
                    break
                if planned.at_breakpoint or planned.step == deadline or planned.step in anticipated:
                    load = planned.cognitive_load if planned.cognitive_load is not None else signals.cognitive_load
                    slots.append((planned.step, planned.action, load, planned.at_breakpoint))

        scheduled = {d.target_step for d in state.pending if d.assumption_id != assumption.id}
        benefit = p_wrong * harm * e_now
        candidates: list[TimingCandidate] = []
        for t, action, load, at_breakpoint in slots:
            batched = t != step and (t in scheduled or t in anticipated)
            cost = cint(load, at_breakpoint, InterventionKind.CLARIFICATION)
            if batched:
                cost *= p.batch_marginal_cost
            rework = p_wrong * sum(rework_cost(d.severity, p) for d in dependents if step <= d.step < t)
            notes = []
            if t == step:
                notes.append("now")
            if at_breakpoint:
                notes.append("natural breakpoint")
            if batched and t in anticipated:
                notes.append("batched with a confirmation that this step will probably need anyway")
            elif batched:
                notes.append("batched with another scheduled question")
            if t == deadline:
                notes.append(
                    f"last moment before '{commitment.action}', which cannot be undone"
                    if commitment is not None
                    else "last step that depends on this assumption"
                )
            candidates.append(
                TimingCandidate(
                    step=t,
                    action=action,
                    feasible=True,
                    benefit=benefit,
                    interruption_cost=cost,
                    rework_cost=rework,
                    at_breakpoint=at_breakpoint,
                    batched=batched,
                    note="; ".join(notes),
                )
            )
        # Ties go to the earliest moment (asking earlier never accumulates rework).
        best = max(candidates, key=lambda c: (round(c.value, 12), -c.step))
        return ItemTiming(
            item_id=f"assumption:{assumption.id}",
            label=assumption.description,
            is_assumption=True,
            deferrable=deferrable,
            commitment_step=commitment.step if commitment is not None else None,
            commitment_action=commitment.action if commitment is not None else None,
            candidates=candidates,
            chosen_step=best.step if best.value > 0 else None,
        )

    def _anticipated_confirmations(self, future: list[PlannedAction], signals: ResolvedSignals) -> set[int]:
        """Planned steps whose own approval is expected to be worth asking for.

        The agent's future confidence is unknown, so ``anticipated_agent_confidence`` is assumed.
        """
        p = self.parameters
        e = catch_probability(signals.habituation, p)
        p_err = clamp01(1.0 - p.anticipated_agent_confidence)
        out: set[int] = set()
        for planned in future:
            severity, recoverability = _planned_signals(planned)
            load = planned.cognitive_load if planned.cognitive_load is not None else signals.cognitive_load
            benefit = p_err * error_cost(severity, recoverability, p) * e
            cost = interruption_cost(
                cognitive_load=load,
                at_breakpoint=planned.at_breakpoint,
                habituation_level=signals.habituation,
                kind=InterventionKind.CONFIRMATION,
                params=p,
                preference_multiplier=self.preference_multiplier,
            )
            if benefit > cost:
                out.add(planned.step)
        return out

    def _worth_it_without_habituation(self, signals: ResolvedSignals, p_act: float, c_act: float) -> bool:
        p = self.parameters
        benefit = p_act * c_act * p.base_catch_probability
        cost = interruption_cost(
            cognitive_load=signals.cognitive_load,
            at_breakpoint=signals.at_breakpoint,
            habituation_level=0.0,
            kind=InterventionKind.CONFIRMATION,
            params=p,
            preference_multiplier=self.preference_multiplier,
        )
        return benefit - cost > 0

    def _ask_reasons(
        self,
        context: ActionContext,
        signals: ResolvedSignals,
        questions: list[Question],
        assumption_items: list[tuple[Assumption, ItemTiming]],
        step: int,
        has_confirmation: bool,
    ) -> list[ReasonCode]:
        reasons: list[ReasonCode] = []
        if has_confirmation:
            reasons += uncertainty_reasons(signals)
            reasons += consequence_reasons(context, signals)
        else:
            reasons.append(ReasonCode.AMBIGUOUS_ASSUMPTION)
            reasons.append(ReasonCode.LOW_INTENT_CONFIDENCE)
        asked = {q.assumption_id for q in questions if q.assumption_id}
        for assumption, timing in assumption_items:
            if assumption.id not in asked or timing.commitment_step is None:
                continue
            if timing.commitment_step == step:
                reasons.append(ReasonCode.COMMITMENT_POINT)
            else:
                reasons.append(ReasonCode.DEPENDENT_COMMITMENT)
        if signals.at_breakpoint:
            reasons.append(ReasonCode.AT_BREAKPOINT)
        if len(questions) > 1:
            reasons.append(ReasonCode.BATCHED_QUESTIONS)
        return reasons

    def _terms(
        self,
        signals: ResolvedSignals,
        p_act: float,
        c_act: float,
        e_now: float,
        cost_act: float,
        b_act: float,
        assumption_items: list[tuple[Assumption, ItemTiming]],
    ) -> dict[str, Any]:
        assumptions: dict[str, Any] = {}
        for assumption, timing in assumption_items:
            best = timing.best
            assumptions[assumption.id] = {
                "p_wrong": 1.0 - assumption.confidence,
                "kind": assumption.kind.value,
                "deferrable": timing.deferrable,
                "commitment_step": timing.commitment_step,
                "best_step": timing.chosen_step,
                "best_value": best.value if best else None,
                "value_now": timing.candidates[0].value,
            }
        return {
            "p_agent_error": signals.p_agent_error,
            "p_intent_error_residual": 1.0 - signals.residual_intent_confidence,
            "p_error_action": p_act,
            "error_cost": c_act,
            "catch_probability": e_now,
            "habituation": signals.habituation,
            "interruption_cost_now": cost_act,
            "benefit_action": b_act,
            "value_action": b_act - cost_act,
            "preference_multiplier": self.preference_multiplier,
            "timing_enabled": self.timing,
            "assumptions": assumptions,
        }


class MyopicVOIPolicy(AdaptivePolicy):
    """Expected value of asking *now* only (no deferral). The ablation baseline for H1b."""

    name = "myopic_voi"
    summary = "Asks whenever asking right now is worth more than it costs; never plans the timing."

    def __init__(
        self,
        parameters: ModelParameters | None = None,
        preferences: UserPreferences | None = None,
        *,
        block_catastrophic: bool = True,
    ) -> None:
        super().__init__(
            parameters, preferences, timing=False, block_catastrophic=block_catastrophic, name="myopic_voi"
        )

    def config(self) -> dict[str, Any]:
        return {"timing": False, "block_catastrophic": self.block_catastrophic}
