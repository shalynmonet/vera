"""
Minimal local call-history log. Appends one JSON record per completed call
to call_log.json in the project root.

This is a plain local file, not a database - if/when this pipeline gets a
real backend, replace this module's storage with that, keeping the same
append_call() signature. Used by dashboard/index.html to render call
history for the local demo UI.
"""

import datetime
import json
from pathlib import Path
from typing import Any

LOG_PATH = Path(__file__).parent / "call_log.json"


def append_call(
    *,
    resident: dict[str, Any],
    call_type: str,
    call_result: dict[str, Any],
    escalation_decision: dict[str, Any],
) -> None:
    entries = _load()
    result_block = call_result.get("result") or {}
    duration = (result_block.get("extracted") or {}).get("calling", {}).get("duration_seconds")

    entries.append(
        {
            "id": call_result.get("run_id") or f"{resident['id']}-{datetime.datetime.now(datetime.UTC).isoformat()}",
            "resident_id": resident["id"],
            "resident_name": resident["name"],
            "call_type": call_type,
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "status": call_result.get("status"),
            "summary": result_block.get("post_summary") or result_block.get("summary"),
            "transcript": result_block.get("transcript"),
            "duration_seconds": duration,
            "escalation": escalation_decision,
        }
    )
    _save(entries)


def _load() -> list[dict[str, Any]]:
    if not LOG_PATH.exists():
        return []
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(entries: list[dict[str, Any]]) -> None:
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)
