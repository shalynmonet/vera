"""
Strands tools for Vera's call orchestration: place_social_checkin_call and
place_activity_call. Both go through CALL-E via calle_cli.py and poll until
the call reaches a terminal status.
"""

import datetime
import time
from typing import Any

from strands import tool

import calle_cli
import call_log
import data_source
import escalation
import templates

TERMINAL_STATUSES = {
    "COMPLETED", "FAILED", "NO_ANSWER", "DECLINED",
    "CANCELED", "CANCELLED", "VOICEMAIL", "BUSY", "EXPIRED",
}

WEEKDAY_KEYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def _poll_until_terminal(run_id: str, poll_seconds: int = 10, max_polls: int = 60) -> dict[str, Any]:
    for attempt in range(max_polls):
        payload = calle_cli.get_call_status(run_id)
        structured = calle_cli.extract_structured_content(payload)
        status = structured.get("status")
        if status in TERMINAL_STATUSES:
            return structured
        activity = structured.get("activity") or []
        if activity:
            last = activity[-1]
            print(f"  [{status}] {last.get('message', '')}")
        if attempt < max_polls - 1:
            time.sleep(poll_seconds)
    raise TimeoutError(f"Call run {run_id} did not reach a terminal status after {max_polls} polls")


def _print_result(resident: dict[str, Any], structured: dict[str, Any]) -> None:
    result = structured.get("result") or {}
    print(f"\n=== Call result: {resident['name']} ===")
    print(f"Status: {structured.get('status')}")
    print(f"Summary: {result.get('post_summary') or result.get('summary') or 'n/a'}")
    duration = (result.get("extracted") or {}).get("calling", {}).get("duration_seconds")
    if duration is not None:
        print(f"Duration: {duration}s")
    transcript = result.get("transcript")
    if transcript:
        print(f"\nTranscript:\n{transcript}")


def _finalize_call(resident: dict[str, Any], structured: dict[str, Any], call_type: str) -> dict[str, Any]:
    """Print the call result, run escalation evaluation, then log it - this
    is the single place both call tools funnel through after a call
    completes."""
    _print_result(resident, structured)
    decision = escalation.handle_call_result(resident, structured)
    if decision["escalate"]:
        print(f"\n\U0001f6a8 ESCALATION: {resident['name']} - {decision['concern_summary']}")
    else:
        print(f"\nEscalation check: routine ({decision['reasoning']})")
    call_log.append_call(
        resident=resident, call_type=call_type, call_result=structured, escalation_decision=decision
    )
    return structured


@tool
def place_social_checkin_call(resident_id: str) -> dict[str, Any]:
    """Place a real warm social check-in call to a resident via CALL-E.

    Looks up the resident, builds the social check-in goal text, places the
    call, polls until it finishes, prints the result, and returns the final
    structured call data.
    """
    resident = data_source.get_resident(resident_id)
    goal = templates.build_social_checkin_goal(resident)
    started = calle_cli.start_call(to_phone=resident["phone"], goal=goal)
    run_id = calle_cli.extract_structured_content(started)["run_id"]
    print(f"Call started for {resident['name']} (run_id={run_id})")
    final = _poll_until_terminal(run_id)
    return _finalize_call(resident, final, call_type="social_checkin")


@tool
def place_activity_call(resident_id: str) -> dict[str, Any] | None:
    """Place a real activity/motivation call for a resident's scheduled
    activity today, via CALL-E.

    Looks up today's entry in the resident's weekly_activity_schedule. On a
    rest day this places a lighter check-in call with no exercise
    encouragement rather than skipping entirely. Polls until the call
    finishes, prints the result, and returns the final structured call data
    (or None if the resident has no schedule entry for today at all).
    """
    resident = data_source.get_resident(resident_id)
    today_key = WEEKDAY_KEYS[datetime.date.today().weekday()]
    today_entry = resident.get("weekly_activity_schedule", {}).get(today_key)

    if today_entry is None:
        print(f"{resident['name']}: no schedule entry for {today_key.title()} - skipping.")
        return None

    if today_entry.get("is_rest_day"):
        print(f"{resident['name']}: {today_key.title()} is a rest day - placing a lighter check-in instead.")
        goal = templates.build_light_activity_goal(resident)
    else:
        goal = templates.build_activity_goal(resident, today_entry)

    started = calle_cli.start_call(to_phone=resident["phone"], goal=goal)
    run_id = calle_cli.extract_structured_content(started)["run_id"]
    print(f"Call started for {resident['name']} (run_id={run_id})")
    final = _poll_until_terminal(run_id)
    return _finalize_call(resident, final, call_type="activity")
