"""
Lambda entry point for Vera's call orchestration.

Event shape:
    {"action": "social_checkin", "resident_id": "resident_1"}
    {"action": "activity", "resident_id": "resident_1"}

Requires: the calle-nodejs-layer (Node.js + @call-e/cli) and a Python deps
layer (strands-agents) both attached to this function, and a
vera/calle-token secret in Secrets Manager (see bootstrap.py).
"""

from typing import Any

import bootstrap
from tools import place_social_checkin_call, place_activity_call

ACTIONS = {
    "social_checkin": place_social_checkin_call,
    "activity": place_activity_call,
}


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    bootstrap.ensure_token_cache()

    action = event.get("action")
    resident_id = event.get("resident_id")
    if action not in ACTIONS:
        raise ValueError(f"Unknown action {action!r}; expected one of {list(ACTIONS)}")
    if not resident_id:
        raise ValueError("resident_id is required")

    result = ACTIONS[action](resident_id=resident_id)
    return {"ok": True, "result": result}
