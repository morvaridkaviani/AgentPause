"""Questionnaire instruments: loading definitions and scoring responses.

Definitions live in ``app/instruments/*.json``. Item text for instruments that cannot be
redistributed (``"redistributable": false``) is loaded from ``INSTRUMENTS_LOCAL_DIR/<id>.json``
if a researcher provides it. Keep that folder out of version control (`instruments-local/` is git-ignored). See docs/experiments.md.
"""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from pathlib import Path
from statistics import fmean
from typing import Any


@lru_cache(maxsize=8)
def _bundled() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    folder = resources.files("app") / "instruments"
    for entry in sorted(folder.iterdir(), key=lambda e: e.name):
        if entry.name.endswith(".json"):
            data = json.loads(entry.read_text(encoding="utf-8"))
            out[data["id"]] = data
    return out


def load_instruments(local_dir: str | None = None) -> dict[str, dict[str, Any]]:
    instruments = {k: dict(v) for k, v in _bundled().items()}
    if local_dir:
        for instrument_id, data in instruments.items():
            path = Path(local_dir) / f"{instrument_id}.json"
            if path.exists():
                local = json.loads(path.read_text(encoding="utf-8"))
                data["items"] = local.get("items", data["items"])
                data["items_source"] = "local"
    for data in instruments.values():
        data.setdefault("items_source", "bundled" if data["items"] else "missing")
        data["ready"] = bool(data["items"])
    return instruments


def score(instrument: dict[str, Any], responses: dict[str, Any]) -> dict[str, Any]:
    method = instrument.get("scoring", {}).get("method", "mean")
    items = instrument.get("items") or []
    scale = instrument.get("scale", {})
    if method == "correct":
        correct = sum(1 for item in items if responses.get(item["id"]) == item.get("correct"))
        answered = sum(1 for item in items if item["id"] in responses)
        return {"correct": correct, "answered": answered, "accuracy": correct / answered if answered else None}
    if method == "sus":
        ids = instrument.get("item_ids") or [item["id"] for item in items]
        sus_values = [float(responses[i]) for i in ids if i in responses]
        if len(sus_values) != 10:
            return {"sus": None, "note": "SUS needs all 10 items"}
        total = sum((v - 1) if n % 2 == 0 else (5 - v) for n, v in enumerate(sus_values))
        return {"sus": total * 2.5}
    # mean (with reverse items and optional subscales)
    lo, hi = float(scale.get("min", 1)), float(scale.get("max", 7))
    values: list[float] = []
    subscales: dict[str, list[float]] = {}
    for item in items:
        if item["id"] not in responses:
            continue
        value = float(responses[item["id"]])
        if not lo <= value <= hi:
            raise ValueError(f"Response {item['id']}={value} outside [{lo}, {hi}]")
        if item.get("reverse"):
            value = lo + hi - value
        values.append(value)
        if item.get("subscale"):
            subscales.setdefault(item["subscale"], []).append(value)
    result: dict[str, Any] = {"mean": fmean(values) if values else None, "answered": len(values)}
    if instrument.get("scoring", {}).get("subscales"):
        result["subscales"] = {k: fmean(v) for k, v in subscales.items()}
    return result
