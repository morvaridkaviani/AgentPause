"""Study mode: participants, counterbalanced condition plans, questionnaires, export.

Design (see research/research_questions.md §5):

* **Policy**: within-subjects. The order is counterbalanced with a balanced Latin square
  (Williams design), so each condition precedes every other equally often for an even number
  of conditions.
* **Scenario**: rotated across blocks. Within every run of ``len(orders)`` consecutive
  participants, each policy meets each scenario equally often (exactly once when there are as
  many scenarios as conditions). The scenario offset shifts every run, so scenario and block
  position are not confounded either.
* **Explanation type**: between-subjects. Participant ``i`` (0-based) gets order ``i mod O`` and
  explanation mode ``(i mod O + i div O) mod M``. Consecutive participants therefore rotate
  through the modes, and each mode receives every condition order once every ``O × M``
  participants (a Latin-square crossing of order and explanation type).

Participants are identified only by random codes. No names, emails, or IP addresses are stored.
"""

from __future__ import annotations

import secrets
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from agentpause.policies import available_policies, canonical_name
from agentpause_sim import load_scenario

from ..models import ParticipantRow, QuestionnaireResponseRow, SessionRow, StudyConfigRow
from ..schemas.api import BlockPlan, ParticipantOut, QuestionnaireIn, StudyConfig
from .instruments import load_instruments, score

_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O/1/I confusion


def williams_square(n: int) -> list[list[int]]:
    """Balanced Latin square (Williams 1949). For odd n, the mirrored rows are appended."""
    if n < 1:
        return []
    first = [0]
    lo, hi = 1, n - 1
    for i in range(1, n):
        if i % 2 == 1:
            first.append(lo)
            lo += 1
        else:
            first.append(hi)
            hi -= 1
    rows = [[(x + r) % n for x in first] for r in range(n)]
    if n % 2 == 1:
        rows += [list(reversed(row)) for row in rows]
    return rows


class StudyService:
    def __init__(self, db: Session, instruments_dir: str | None = None) -> None:
        self.db = db
        self.instruments_dir = instruments_dir

    # ---- configuration -----------------------------------------------------------------
    def config(self) -> StudyConfig:
        row = self.db.get(StudyConfigRow, 1)
        return StudyConfig(**row.config) if row else StudyConfig()

    def update_config(self, config: StudyConfig) -> StudyConfig:
        registered = {p["name"] for p in available_policies()}
        unknown = [c for c in config.conditions if canonical_name(c) not in registered]
        if unknown:
            raise HTTPException(status_code=422, detail=f"Unknown policies in conditions: {unknown}")
        try:
            for sid in [*config.scenarios, *([config.practice_scenario] if config.practice_scenario else [])]:
                load_scenario(sid)
        except KeyError as err:
            raise HTTPException(status_code=422, detail=str(err)) from err
        instruments = load_instruments(self.instruments_dir)
        missing = [i for i in config.post_task_instruments + config.final_instruments if i not in instruments]
        if missing:
            raise HTTPException(status_code=422, detail=f"Unknown instruments: {missing}")
        if not config.conditions or not config.scenarios or not config.explanation_modes:
            raise HTTPException(status_code=422, detail="conditions, scenarios and explanation_modes must be non-empty")
        row = self.db.get(StudyConfigRow, 1)
        if row is None:
            row = StudyConfigRow(id=1, config=config.model_dump())
            self.db.add(row)
        else:
            row.config = config.model_dump()
        self.db.commit()
        return config

    # ---- participants ------------------------------------------------------------------
    def create_participant(self) -> ParticipantRow:
        config = self.config()
        number = int(self.db.scalar(select(func.count()).select_from(ParticipantRow)) or 0) + 1
        code = "P-" + "".join(secrets.choice(_CODE_ALPHABET) for _ in range(6))
        while self.db.get(ParticipantRow, code) is not None:
            code = "P-" + "".join(secrets.choice(_CODE_ALPHABET) for _ in range(6))
        square = williams_square(len(config.conditions))
        index = number - 1
        order_index, cycle = index % len(square), index // len(square)
        order = square[order_index]
        offset = cycle % len(config.scenarios)
        plan: list[dict[str, Any]] = []
        block = 0
        if config.practice_scenario:
            plan.append(
                BlockPlan(
                    block=block,
                    policy="always_confirm",
                    scenario_id=config.practice_scenario,
                    seed=config.seed_base,
                    practice=True,
                ).model_dump()
            )
            block += 1
        for position, condition_index in enumerate(order):
            scenario = config.scenarios[(position + offset) % len(config.scenarios)]
            plan.append(
                BlockPlan(
                    block=block,
                    policy=config.conditions[condition_index],
                    scenario_id=scenario,
                    seed=config.seed_base + number * 100 + position,
                ).model_dump()
            )
            block += 1
        mode = config.explanation_modes[(order_index + cycle) % len(config.explanation_modes)]
        row = ParticipantRow(code=code, number=number, explanation_mode=mode, plan=plan)
        self.db.add(row)
        self.db.commit()
        return row

    def participant(self, code: str) -> ParticipantRow:
        row = self.db.get(ParticipantRow, code)
        if row is None:
            raise HTTPException(status_code=404, detail="Unknown participant code")
        return row

    @staticmethod
    def participant_out(row: ParticipantRow) -> ParticipantOut:
        return ParticipantOut(
            code=row.code,
            number=row.number,
            explanation_mode=row.explanation_mode,
            plan=[BlockPlan(**b) for b in row.plan],
            consented=row.consented,
            completed=row.completed,
        )

    def block(self, code: str, block: int) -> tuple[ParticipantRow, dict[str, Any]]:
        row = self.participant(code)
        if not row.consented:
            raise HTTPException(status_code=403, detail="Consent has not been recorded for this participant")
        if block < 0 or block >= len(row.plan):
            raise HTTPException(status_code=422, detail=f"Block {block} is not in this participant's plan")
        return row, row.plan[block]

    # ---- questionnaires ----------------------------------------------------------------
    def instruments(self) -> dict[str, dict[str, Any]]:
        return load_instruments(self.instruments_dir)

    def record_response(self, req: QuestionnaireIn) -> QuestionnaireResponseRow:
        self.participant(req.participant_code)
        instruments = self.instruments()
        instrument = instruments.get(req.instrument_id)
        if instrument is None:
            raise HTTPException(status_code=404, detail=f"Unknown instrument {req.instrument_id}")
        try:
            result = score(instrument, dict(req.responses))
        except ValueError as err:
            raise HTTPException(status_code=422, detail=str(err)) from err
        policy = None
        if req.session_id:
            session = self.db.get(SessionRow, req.session_id)
            policy = session.policy if session else None
        row = QuestionnaireResponseRow(
            participant_code=req.participant_code,
            session_id=req.session_id,
            block=req.block,
            policy=policy,
            instrument_id=req.instrument_id,
            responses=dict(req.responses),
            score=result,
        )
        self.db.add(row)
        self.db.commit()
        return row

    # ---- export ------------------------------------------------------------------------
    def export_rows(self) -> list[dict[str, Any]]:
        """One row per questionnaire response, joined with the participant's condition data."""
        out: list[dict[str, Any]] = []
        participants = {p.code: p for p in self.db.scalars(select(ParticipantRow))}
        for r in self.db.scalars(select(QuestionnaireResponseRow).order_by(QuestionnaireResponseRow.id)):
            p = participants.get(r.participant_code)
            out.append(
                {
                    "participant_code": r.participant_code,
                    "participant_number": p.number if p else None,
                    "explanation_mode": p.explanation_mode if p else None,
                    "block": r.block,
                    "policy": r.policy,
                    "session_id": r.session_id,
                    "instrument_id": r.instrument_id,
                    "responses": r.responses,
                    "score": r.score,
                    "created_at": r.created_at.isoformat(),
                }
            )
        return out
