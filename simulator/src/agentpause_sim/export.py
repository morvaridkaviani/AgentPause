"""CSV/JSON export. No personally identifiable information is ever written."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

from .experiment import ExperimentResult

RECORD_COLUMNS: tuple[str, ...] = (
    "participant_id",
    "scenario",
    "policy",
    "condition",
    "seed",
    "episode",
    "step_index",
    "attempt",
    "step_id",
    "action",
    "category",
    "decision",
    "score",
    "decision_confidence",
    "reason_codes",
    "intervention",
    "necessary",
    "error_present",
    "n_questions",
    "n_deferred",
    "severity",
    "recoverability",
    "agent_confidence",
    "intent_confidence",
    "cognitive_load",
    "external_effects",
    "at_breakpoint",
    "task_progress",
    "habituation",
    "decision_latency_ms",
    "sim_time_s",
    "user_response",
    "response_time_s",
    "task_success",
    "task_duration_s",
    "subjective_rating",
)


def rows_to_csv(rows: Iterable[dict[str, Any]], columns: Sequence[str] | None = None) -> str:
    rows = list(rows)
    if columns is None:
        if not rows or "step_index" in rows[0]:
            columns = list(RECORD_COLUMNS)  # empty exports still get the documented header
        else:
            columns = sorted({k for r in rows for k in r})
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(columns), extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: _cell(row.get(k)) for k in columns})
    return buffer.getvalue()


def _cell(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    if isinstance(value, float):
        return round(value, 6)
    return value


def write_result(result: ExperimentResult, out_dir: str | Path) -> dict[str, Path]:
    """Write records.csv, episodes.csv, summary.json, and config.json to ``out_dir``."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = {
        "records": out / "records.csv",
        "episodes": out / "episodes.csv",
        "summary": out / "summary.json",
        "config": out / "config.json",
    }
    paths["records"].write_text(rows_to_csv(result.records), encoding="utf-8")
    paths["episodes"].write_text(rows_to_csv([s.to_dict() for s in result.summaries]), encoding="utf-8")
    paths["summary"].write_text(json.dumps(result.to_dict(), indent=2, default=str), encoding="utf-8")
    paths["config"].write_text(json.dumps(result.config.to_dict(), indent=2), encoding="utf-8")
    return paths
