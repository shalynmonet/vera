"""
Resident data source for Vera's call orchestration.

This is the single swappable seam between mock data and the real Lovable
export endpoint. Every caller in this project goes through get_resident()
and list_residents() below - nothing else touches mock_residents.json
directly. To switch to the real API once its auth bug is fixed, replace the
bodies of _load_residents() (and nothing else) with an HTTP call to
https://vera-cares.lovable.app/api/public/vera-export, keeping the same
return shape (a list of resident dicts with the fields below).
"""

import json
from pathlib import Path
from typing import Any

MOCK_DATA_PATH = Path(__file__).parent / "mock_residents.json"

# Required fields on every resident dict, kept here so a swapped-in real
# data source can be checked against the same shape this project expects.
REQUIRED_RESIDENT_FIELDS = (
    "id",
    "name",
    "phone",
    "living_situation",
    "family_contact",
    "caregiver_contact",
    "notes",
    "call_schedules",
    "weekly_activity_schedule",
)


def _load_residents() -> list[dict[str, Any]]:
    """The swappable part. Currently reads mock_residents.json.

    Replace this function body with a call to the real export endpoint,
    e.g.:

        import requests
        resp = requests.get(
            "https://vera-cares.lovable.app/api/public/vera-export",
            headers={"Authorization": f"Bearer {VERA_EXPORT_API_KEY}"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["residents"]

    Keep the return shape identical (a list of resident dicts) and every
    caller elsewhere in this project keeps working unchanged.
    """
    with open(MOCK_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def list_residents() -> list[dict[str, Any]]:
    """Return all known residents."""
    return _load_residents()


def get_resident(resident_id: str) -> dict[str, Any]:
    """Return one resident by id, or raise KeyError if not found."""
    for resident in _load_residents():
        if resident["id"] == resident_id:
            return resident
    raise KeyError(f"No resident found with id={resident_id!r}")
