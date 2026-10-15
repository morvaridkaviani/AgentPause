"""Interactive sessions.

* **simulated** sessions (demo and study modes) run a scenario with the episode engine. A
  person responds to the intervention cards.
* **external** sessions (api mode) let any agent submit its own actions through
  ``POST /api/v1/action``.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from agentpause import ActionContext, AgentPause, Decision, ResponseType
from agentpause_sim import EngineError, EpisodeEngine, HumanResponse, load_scenario, summarize

from ..models import EventRow, InterventionRow, SessionRow
from ..schemas.api import SessionCreate, SessionOut, StepInfo, TimelineItem
from ..schemas.common import ActionContextIn, EventOut
from .common import build_policy, iso, normalize_spec, present_decision, risk_level, strip_ground_truth

MAX_RESPONSE_SECONDS = 600.0


def _now() -> datetime:
    return datetime.now(UTC)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


class SessionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ---- lookup --------------------------------------------------------------------------
    def get(self, session_id: str) -> SessionRow:
        row = self.db.get(SessionRow, session_id)
        if row is None:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        return row

    def engine(self, row: SessionRow) -> EpisodeEngine:
        if row.kind != "simulated" or row.scenario_id is None:
            raise HTTPException(status_code=409, detail="This session has no simulated agent; use POST /api/v1/action")
        return EpisodeEngine.from_dict(row.state, load_scenario(row.scenario_id))

    # ---- creation ------------------------------------------------------------------------
    def create(
        self, req: SessionCreate, *, plan_block: dict[str, Any] | None = None, explanation_mode: str | None = None
    ) -> SessionRow:
        spec = normalize_spec(req.policy, req.preferences)
        scenario_id = req.scenario_id
        seed = req.seed if req.seed is not None else secrets.randbelow(2**31)
        if plan_block is not None:
            spec = normalize_spec(plan_block["policy"])
            scenario_id = plan_block["scenario_id"]
            seed = plan_block["seed"]
        policy = build_policy(spec)
        row = SessionRow(
            id=str(uuid.uuid4()),
            mode=req.mode,
            policy=policy.name,
            policy_spec=spec,
            scenario_id=None,
            seed=seed,
            episode=req.episode,
            participant_code=req.participant_code,
            condition=req.condition or (plan_block or {}).get("policy"),
            block=req.block,
            explanation_mode=explanation_mode or req.explanation_mode,
            status="running",
            step_index=0,
            state={},
        )
        if req.mode in ("demo", "study"):
            if not scenario_id:
                raise HTTPException(status_code=422, detail="scenario_id is required for demo and study sessions")
            try:
                scenario = load_scenario(scenario_id)
            except KeyError as err:
                raise HTTPException(status_code=404, detail=str(err)) from err
            engine = EpisodeEngine(
                scenario,
                AgentPause(policy, explain="full"),
                seed=seed,
                episode=req.episode,
                condition=row.condition or "default",
            )
            row.kind = "simulated"
            row.scenario_id = scenario.id
            row.state = engine.to_dict()
        else:
            row.kind = "external"
            row.state = {"pause": AgentPause(policy, explain="full").to_dict(), "pending": None, "sequence": 0}
        self.db.add(row)
        self.db.flush()
        self._persist(
            row, [{"seq": 0, "type": "session_created", "policy": row.policy, "scenario_id": row.scenario_id}]
        )
        self.db.commit()
        return row

    # ---- simulated agent -----------------------------------------------------------------
    def step(
        self, row: SessionRow, until: str = "next"
    ) -> tuple[list[EventRow], dict[str, Any] | None, dict[str, Any] | None]:
        engine = self.engine(row)
        if engine.state.status == "awaiting_human":
            raise HTTPException(status_code=409, detail="An intervention is awaiting your response")
        if engine.done:
            raise HTTPException(status_code=409, detail=f"Session is {engine.state.status}")
        events: list[dict[str, Any]] = []
        decision: dict[str, Any] | None = None
        card: dict[str, Any] | None = None
        for _ in range(60):
            result = engine.step()
            events += result.events
            if result.decision is not None:
                decision = result.decision.to_dict()
            if result.card is not None:
                card = engine.public_pending()
                self.db.add(
                    InterventionRow(
                        intervention_id=result.card["intervention_id"],
                        session_id=row.id,
                        step_index=result.card["step_index"],
                        decision=result.card["decision"],
                    )
                )
                break
            if engine.done or until == "next":
                break
        self._save_engine(row, engine)
        saved = self._persist(row, events)
        self.db.commit()
        return saved, decision, card

    def respond(
        self, row: SessionRow, response_name: str, answers: dict[str, str], intervention_id: str | None
    ) -> tuple[list[EventRow], dict[str, Any] | None]:
        response = ResponseType(response_name)
        if row.kind == "external":
            return self._respond_external(row, response, answers, intervention_id)
        engine = self.engine(row)
        pending = engine.state.pending
        if pending is None:
            raise HTTPException(status_code=409, detail="No intervention is awaiting a response")
        if intervention_id and intervention_id != pending["intervention_id"]:
            raise HTTPException(status_code=409, detail="That intervention is no longer pending")
        allowed = set(pending["allowed_responses"]) | {"timeout"}
        if response.value not in allowed:
            raise HTTPException(
                status_code=422, detail=f"Response '{response.value}' not allowed here; use one of {sorted(allowed)}"
            )
        irow = self._intervention(row, pending["intervention_id"])
        elapsed = 0.0
        if irow is not None:
            elapsed = min(MAX_RESPONSE_SECONDS, (_now() - _aware(irow.created_at)).total_seconds())
        try:
            result = engine.respond(HumanResponse(response, answers=answers, response_time_s=elapsed, source="human"))
        except EngineError as err:
            raise HTTPException(status_code=409, detail=str(err)) from err
        if irow is not None:
            if response == ResponseType.ASK_WHY:
                irow.why_requests += 1
            else:
                irow.resolved_at = _now()
                irow.response = response.value
                irow.answers = answers
                irow.response_time_s = elapsed
        self._save_engine(row, engine)
        saved = self._persist(row, result.events)
        self.db.commit()
        return saved, pending["decision"]

    def _save_engine(self, row: SessionRow, engine: EpisodeEngine) -> None:
        row.state = engine.to_dict()
        row.status = engine.state.status
        row.step_index = engine.state.index
        if engine.done:
            summary = summarize(engine.state, len(engine.scenario.steps)).to_dict()
            row.outcome = {**engine.outcome(), "summary": summary}

    # ---- external agent ------------------------------------------------------------------
    def action(self, row: SessionRow, context_in: ActionContextIn) -> tuple[Decision, str | None, list[EventRow]]:
        if row.kind != "external":
            raise HTTPException(
                status_code=409, detail="Simulated sessions are driven by POST /api/v1/session/{id}/step"
            )
        state = dict(row.state)
        if state.get("pending"):
            raise HTTPException(
                status_code=409, detail="Respond to the pending intervention first (POST /api/v1/intervention)"
            )
        pause = AgentPause.from_dict(state["pause"])
        try:
            context = ActionContext.build(context_in.action, **context_in.to_engine_kwargs())
        except (ValueError, TypeError) as err:
            raise HTTPException(status_code=422, detail=str(err)) from err
        decision = pause.evaluate(context=context)
        state["sequence"] = int(state.get("sequence", 0)) + 1
        payload = {
            "seq": state["sequence"],
            "type": "decision",
            "step": decision.step,
            "label": context.action,
            "description": context.description,
            "decision": decision.to_dict(),
            "record": {
                "action": context.action,
                "intervention": decision.interrupts,
                "severity": decision.signals.get("severity"),
                "recoverability": decision.signals.get("recoverability"),
                "decision_latency_ms": decision.latency_ms,
            },
        }
        events = [payload]
        intervention_id = None
        if decision.interrupts:
            intervention_id = f"{row.id}-{state['sequence']}"
            state["pending"] = {"intervention_id": intervention_id, "decision": decision.to_dict()}
            self.db.add(
                InterventionRow(
                    intervention_id=intervention_id,
                    session_id=row.id,
                    step_index=decision.step,
                    decision=decision.to_dict(),
                )
            )
            row.status = "awaiting_human"
            state["sequence"] += 1
            events.append(
                {
                    "seq": state["sequence"],
                    "type": "intervention",
                    "step": decision.step,
                    "intervention_id": intervention_id,
                }
            )
        state["pause"] = pause.to_dict()
        row.state = state
        row.step_index = pause.state.step
        saved = self._persist(row, events)
        self.db.commit()
        return decision, intervention_id, saved

    def _respond_external(
        self, row: SessionRow, response: ResponseType, answers: dict[str, str], intervention_id: str | None
    ) -> tuple[list[EventRow], dict[str, Any] | None]:
        state = dict(row.state)
        pending = state.get("pending")
        if not pending:
            raise HTTPException(status_code=409, detail="No intervention is awaiting a response")
        if intervention_id and intervention_id != pending["intervention_id"]:
            raise HTTPException(status_code=409, detail="That intervention is no longer pending")
        decision_dict = pending["decision"]
        state["sequence"] = int(state.get("sequence", 0)) + 1
        events = [
            {
                "seq": state["sequence"],
                "type": "response" if response != ResponseType.ASK_WHY else "ask_why",
                "step": decision_dict["step"],
                "response": {"response": response.value, "answers": answers},
            }
        ]
        irow = self._intervention(row, pending["intervention_id"])
        if response != ResponseType.ASK_WHY:
            pause = AgentPause.from_dict(state["pause"])
            pause.respond(Decision.from_dict(decision_dict), response, answers=answers)
            state["pause"] = pause.to_dict()
            state["pending"] = None
            row.status = "running"
            if irow is not None:
                irow.resolved_at = _now()
                irow.response = response.value
                irow.answers = answers
                irow.response_time_s = min(MAX_RESPONSE_SECONDS, (_now() - _aware(irow.created_at)).total_seconds())
        elif irow is not None:
            irow.why_requests += 1
        row.state = state
        saved = self._persist(row, events)
        self.db.commit()
        return saved, decision_dict

    def _intervention(self, row: SessionRow, intervention_id: str) -> InterventionRow | None:
        stmt = select(InterventionRow).where(
            InterventionRow.session_id == row.id, InterventionRow.intervention_id == intervention_id
        )
        return self.db.scalars(stmt).first()

    # ---- events --------------------------------------------------------------------------
    def _persist(self, row: SessionRow, events: list[dict[str, Any]]) -> list[EventRow]:
        saved: list[EventRow] = []
        base = self.db.scalar(select(func.coalesce(func.max(EventRow.seq), -1)).where(EventRow.session_id == row.id))
        next_seq = int(base if base is not None else -1) + 1
        for event in events:
            decision = event.get("decision") if event.get("type") == "decision" else None
            record = event.get("record") or {}
            response = (event.get("response") or {}).get("response") if event.get("type") == "response" else None
            event_row = EventRow(
                session_id=row.id,
                seq=next_seq,
                type=str(event.get("type")),
                mode=row.mode,
                scenario_id=row.scenario_id,
                policy=row.policy,
                participant_code=row.participant_code,
                condition=row.condition,
                step_index=event.get("step"),
                action=record.get("action") or (decision or {}).get("action"),
                decision=(decision or {}).get("decision"),
                score=(decision or {}).get("score"),
                intervention=bool(record.get("intervention")) if decision else False,
                risk_level=risk_level(record.get("severity"), record.get("recoverability")) if decision else None,
                user_response=response,
                latency_ms=record.get("decision_latency_ms") if decision else None,
                payload=event,
            )
            next_seq += 1
            self.db.add(event_row)
            saved.append(event_row)
        self.db.flush()
        return saved

    def events(self, row: SessionRow, since: int = -1) -> list[EventRow]:
        stmt = select(EventRow).where(EventRow.session_id == row.id, EventRow.seq > since).order_by(EventRow.seq)
        return list(self.db.scalars(stmt))

    # ---- presentation --------------------------------------------------------------------
    def event_out(self, row: SessionRow, event: EventRow) -> EventOut:
        payload = dict(event.payload)
        if row.mode == "study":
            payload = strip_ground_truth(payload)
            if "decision" in payload and isinstance(payload["decision"], dict):
                payload["decision"] = present_decision(payload["decision"], row.explanation_mode)
        return EventOut(
            id=event.id,
            seq=event.seq,
            session_id=event.session_id,
            created_at=iso(event.created_at) or "",
            type=event.type,
            mode=event.mode,
            scenario_id=event.scenario_id,
            policy=event.policy,
            participant_code=event.participant_code,
            condition=event.condition,
            step_index=event.step_index,
            action=event.action,
            decision=event.decision,
            score=event.score,
            intervention=event.intervention,
            risk_level=event.risk_level,
            user_response=event.user_response,
            latency_ms=event.latency_ms,
            payload=payload,
        )

    def timeline(self, row: SessionRow, events: list[EventRow]) -> list[TimelineItem]:
        items: list[TimelineItem] = []
        study = row.mode == "study"
        for event in events:
            payload = event.payload
            if event.type == "decision":
                decision = payload["decision"]
                signals = decision.get("signals", {})
                presented = present_decision(decision, row.explanation_mode) if study else decision
                items.append(
                    TimelineItem(
                        seq=event.seq,
                        step_index=event.step_index or 0,
                        step_id=payload.get("step_id"),
                        label=payload.get("label") or event.action or "",
                        description=payload.get("description", ""),
                        decision=decision["decision"],
                        score=decision["score"],
                        confidence=decision.get("confidence"),
                        risk_level=event.risk_level or "unknown",
                        signals={
                            k: signals.get(k)
                            for k in (
                                "agent_confidence",
                                "intent_confidence",
                                "severity",
                                "recoverability",
                                "cognitive_load",
                                "at_breakpoint",
                                "external_effects",
                                "provenance",
                            )
                        },
                        reason_codes=(presented or {}).get("reason_codes", []),
                        explanation=(presented or {}).get("explanation", ""),
                        n_questions=len(decision.get("questions", [])),
                        deferred=decision.get("deferred", []),
                        decision_detail=presented,  # type: ignore[arg-type]
                    )
                )
            elif event.type == "response" and items:
                target = next((i for i in reversed(items) if i.step_index == event.step_index), None)
                if target is not None:
                    target.response = (payload.get("response") or {}).get("response")
            elif event.type == "executed" and items:
                target = next((i for i in reversed(items) if i.step_index == event.step_index), None)
                if target is not None:
                    target.executed = True
                    target.harm = None if study else list(payload.get("harm", []))
            elif event.type == "skipped":
                items.append(
                    TimelineItem(
                        seq=event.seq,
                        step_index=event.step_index or 0,
                        step_id=payload.get("step_id"),
                        label=payload.get("label", ""),
                        description=payload.get("reason", ""),
                        decision="SKIPPED",
                        score=0.0,
                        risk_level="low",
                        skipped=True,
                    )
                )
        return items

    def to_out(self, row: SessionRow) -> SessionOut:
        events = self.events(row)
        study = row.mode == "study"
        scenario_info = None
        brief = None
        steps: list[StepInfo] = []
        pending = None
        pending_questions: list[dict[str, Any]] = []
        n_steps = 0
        if row.kind == "simulated" and row.scenario_id:
            engine = self.engine(row)
            sc = engine.scenario
            scenario_info = sc.summary()
            brief = engine.brief()
            n_steps = len(sc.steps)
            steps = [
                StepInfo(
                    index=i,
                    id=s.id,
                    label=s.label,
                    subtask=s.subtask,
                    category=s.category.value,
                    reversible=s.reversible,
                    breakpoint=s.breakpoint,
                    requires_human_input=s.requires_human_input,
                )
                for i, s in enumerate(sc.steps)
            ]
            pending = engine.public_pending()
            pending_questions = [d.to_dict() for d in engine.pause.pending_questions]
        else:
            stored = (row.state or {}).get("pending")
            pending = {"intervention_id": stored["intervention_id"], "decision": stored["decision"]} if stored else None
            pause_state = (row.state or {}).get("pause", {}).get("state", {})
            pending_questions = list(pause_state.get("pending", []))
        if pending and study:
            pending = strip_ground_truth(pending)
            pending["decision"] = present_decision(pending["decision"], row.explanation_mode)
        outcome = row.outcome
        if study and outcome is not None:
            outcome = {"status": outcome.get("status"), "task_duration_s": outcome.get("task_duration_s")}
        return SessionOut(
            id=row.id,
            created_at=iso(row.created_at) or "",
            mode=row.mode,
            kind=row.kind,
            policy=row.policy,
            policy_spec=row.policy_spec,
            explanation_mode=row.explanation_mode,
            scenario=scenario_info,
            brief=brief,
            status=row.status,
            step_index=row.step_index,
            n_steps=n_steps,
            steps=steps,
            timeline=self.timeline(row, events),
            pending=pending,
            pending_questions=pending_questions,
            outcome=outcome,
            participant_code=row.participant_code,
            block=row.block,
            seed=row.seed,
            episode=row.episode,
        )
