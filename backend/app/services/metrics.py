"""Research dashboard metrics: aggregates and chart data with filters.

Sources:

* ``experiment``: a completed simulation experiment (default: the most recent one).
* ``sessions``: completed interactive sessions (demo and/or study), i.e. real human responses
  to simulated agents.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import fmean
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from agentpause.explain.reasons import phrase
from agentpause_sim import EpisodeEngine, load_scenario, metric_catalog, summarize
from agentpause_sim.metrics import EpisodeSummary, aggregate

from ..models import EventRow, ExperimentEpisodeRow, ExperimentRecordRow, ExperimentRow, SessionRow
from .common import risk_level

PROGRESS_BINS = [
    (0.0, 0.2, "0–20%"),
    (0.2, 0.4, "20–40%"),
    (0.4, 0.6, "40–60%"),
    (0.6, 0.8, "60–80%"),
    (0.8, 1.01, "80–100%"),
]


def _summary_from_dict(data: dict[str, Any]) -> EpisodeSummary:
    fields = EpisodeSummary.__dataclass_fields__
    return EpisodeSummary(**{k: data[k] for k in fields if k in data})


def _bin(progress: float | None) -> str:
    p = 0.0 if progress is None else float(progress)
    for lo, hi, label in PROGRESS_BINS:
        if lo <= p < hi:
            return label
    return PROGRESS_BINS[-1][2]


def compute_metrics(
    db: Session,
    *,
    source: str = "experiment",
    experiment_id: str | None = None,
    scenario: str | None = None,
    policy: str | None = None,
    participant: str | None = None,
    condition: str | None = None,
    risk: str | None = None,
    mode: str | None = None,
) -> dict[str, Any]:
    filters = {
        "source": source,
        "experiment_id": experiment_id,
        "scenario": scenario,
        "policy": policy,
        "participant": participant,
        "condition": condition,
        "risk_level": risk,
        "mode": mode,
    }
    summaries: list[EpisodeSummary] = []
    records: list[dict[str, Any]] = []
    available: dict[str, list[Any]] = {}
    experiments = list(
        db.scalars(
            select(ExperimentRow).where(ExperimentRow.status == "completed").order_by(ExperimentRow.created_at.desc())
        )
    )
    available["experiments"] = [
        {"id": e.id, "name": e.name, "created_at": e.created_at.isoformat()} for e in experiments
    ]

    if source == "experiment":
        if experiment_id is None and experiments:
            experiment_id = experiments[0].id
            filters["experiment_id"] = experiment_id
        if experiment_id is not None:
            ep_stmt = select(ExperimentEpisodeRow).where(ExperimentEpisodeRow.experiment_id == experiment_id)
            rec_stmt = select(ExperimentRecordRow).where(ExperimentRecordRow.experiment_id == experiment_id)
            all_eps = list(db.scalars(ep_stmt))
            available["scenarios"] = sorted({e.scenario_id for e in all_eps})
            available["policies"] = sorted({e.policy for e in all_eps})
            available["conditions"] = sorted({e.condition for e in all_eps})
            available["participants"] = []
            for e in all_eps:
                if (
                    (scenario and e.scenario_id != scenario)
                    or (policy and e.policy != policy)
                    or (condition and e.condition != condition)
                ):
                    continue
                summaries.append(_summary_from_dict(e.data))
            if scenario:
                rec_stmt = rec_stmt.where(ExperimentRecordRow.scenario_id == scenario)
            if policy:
                rec_stmt = rec_stmt.where(ExperimentRecordRow.policy == policy)
            if condition:
                rec_stmt = rec_stmt.where(ExperimentRecordRow.condition == condition)
            if risk:
                rec_stmt = rec_stmt.where(ExperimentRecordRow.risk_level == risk)
            records = [dict(r.data) for r in db.scalars(rec_stmt)]
    else:
        stmt = select(SessionRow).where(SessionRow.kind == "simulated", SessionRow.status == "completed")
        if mode:
            stmt = stmt.where(SessionRow.mode == mode)
        rows = list(db.scalars(stmt))
        available["scenarios"] = sorted({r.scenario_id for r in rows if r.scenario_id})
        available["policies"] = sorted({r.policy for r in rows})
        available["conditions"] = sorted({r.condition for r in rows if r.condition})
        available["participants"] = sorted({r.participant_code for r in rows if r.participant_code})
        for row in rows:
            if (scenario and row.scenario_id != scenario) or (policy and row.policy != policy):
                continue
            if (participant and row.participant_code != participant) or (condition and row.condition != condition):
                continue
            engine = EpisodeEngine.from_dict(row.state, load_scenario(row.scenario_id or ""))
            summary = summarize(engine.state, len(engine.scenario.steps))
            summary.policy = row.policy
            summary.condition = row.mode
            summary.participant_id = row.participant_code or f"demo-{row.id[:8]}"
            summaries.append(summary)
            for record in engine.state.records:
                if risk and risk_level(record.get("severity"), record.get("recoverability")) != risk:
                    continue
                records.append({**record, "policy": row.policy, "participant_id": summary.participant_id})

    aggregates = aggregate(summaries, group_by=("policy",), n_boot=200) if summaries else []
    return {
        "source": source,
        "filters": filters,
        "n_episodes": len(summaries),
        "aggregates": aggregates,
        "charts": _charts(records, aggregates),
        "available": available,
        "metric_definitions": metric_catalog(),
        "note": "SIMULATED RESULTS. Not evaluated with human participants."
        if source == "experiment"
        else "Human responses to simulated agents (demo/study sessions).",
    }


def _charts(records: list[dict[str, Any]], aggregates: list[dict[str, Any]]) -> dict[str, Any]:
    policies = sorted({r["policy"] for r in records} | {a["policy"] for a in aggregates})
    decisions_by_policy: dict[str, Counter[str]] = defaultdict(Counter)
    timing: dict[tuple[str, str], int] = Counter()
    interventions_per_policy: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    reasons_by_policy: dict[str, Counter[str]] = defaultdict(Counter)
    risk: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])
    responses: dict[str, Counter[str]] = defaultdict(Counter)
    uncertainty: dict[tuple[str, str], list[tuple[float, float]]] = defaultdict(list)
    for r in records:
        policy = r["policy"]
        decision = r["decision"]
        decisions_by_policy[policy][decision] += 1
        level = risk_level(r.get("severity"), r.get("recoverability"))
        risk[(policy, level)][0] += 1
        if r.get("agent_confidence") is not None:
            uncertainty[(policy, decision)].append(
                (float(r["agent_confidence"]), float(r.get("intent_confidence") or 0.0))
            )
        if r.get("intervention"):
            interventions_per_policy[policy] += 1
            timing[(policy, _bin(r.get("task_progress")))] += 1
            risk[(policy, level)][1] += 1
            for code in str(r.get("reason_codes") or "").split(";"):
                if code and code not in ("MISSING_SIGNAL_DEFAULTED",):
                    reasons[code] += 1
                    reasons_by_policy[policy][code] += 1
        if r.get("user_response"):
            responses[policy][r["user_response"]] += 1
    return {
        "policies": policies,
        "decisions_by_policy": [{"policy": p, **dict(decisions_by_policy[p])} for p in policies],
        "intervention_timing": [
            {
                "policy": p,
                "bin": label,
                "count": timing[(p, label)],
                "share": timing[(p, label)] / interventions_per_policy[p] if interventions_per_policy[p] else 0.0,
            }
            for p in policies
            for _, _, label in PROGRESS_BINS
        ],
        "reasons": [{"code": c, "phrase": phrase(c), "count": n} for c, n in reasons.most_common(12)],
        "reasons_by_policy": {
            p: [{"code": c, "count": n} for c, n in reasons_by_policy[p].most_common(6)] for p in policies
        },
        "risk": [
            {
                "policy": p,
                "risk_level": level,
                "decisions": v[0],
                "interventions": v[1],
                "rate": v[1] / v[0] if v[0] else 0.0,
            }
            for (p, level), v in sorted(risk.items())
        ],
        "responses": [{"policy": p, **dict(responses[p])} for p in policies if responses[p]],
        "uncertainty": [
            {
                "policy": p,
                "decision": d,
                "n": len(v),
                "mean_agent_confidence": fmean(a for a, _ in v),
                "mean_intent_confidence": fmean(b for _, b in v),
            }
            for (p, d), v in sorted(uncertainty.items())
            if v
        ],
        "summary": [
            {
                "policy": a["policy"],
                **{
                    k: a.get(k)
                    for k in (
                        "episodes",
                        "interventions",
                        "questions",
                        "deferrals",
                        "unnecessary_rate",
                        "missed_rate",
                        "recovery_rate",
                        "harm",
                        "task_success",
                        "task_duration_s",
                        "override_rate",
                        "acceptance_rate",
                        "rework_steps",
                        "human_error_rate",
                        "decision_latency_ms",
                        "workload_proxy",
                    )
                },
            }
            for a in aggregates
        ],
    }


def event_query(
    db: Session,
    *,
    session_id: str | None = None,
    mode: str | None = None,
    scenario: str | None = None,
    policy: str | None = None,
    participant: str | None = None,
    decision: str | None = None,
    risk: str | None = None,
    type_: str | None = None,
    interventions_only: bool = False,
) -> Any:
    stmt = select(EventRow)
    if session_id:
        stmt = stmt.where(EventRow.session_id == session_id)
    if mode:
        stmt = stmt.where(EventRow.mode == mode)
    if scenario:
        stmt = stmt.where(EventRow.scenario_id == scenario)
    if policy:
        stmt = stmt.where(EventRow.policy == policy)
    if participant:
        stmt = stmt.where(EventRow.participant_code == participant)
    if decision:
        stmt = stmt.where(EventRow.decision == decision)
    if risk:
        stmt = stmt.where(EventRow.risk_level == risk)
    if type_:
        stmt = stmt.where(EventRow.type == type_)
    if interventions_only:
        stmt = stmt.where(EventRow.intervention.is_(True))
    return stmt
