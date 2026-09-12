"""
Tests the full handle_call_result path (judgment + email send) against the
escalation mock scenario. Sends a real email via Resend to resident_1's
caregiver_contact (Shalyn's own address).
"""

import data_source
from escalation import handle_call_result
from test_escalation import ESCALATION_CALL_RESULT


def main() -> None:
    resident = data_source.get_resident("resident_1")
    print(f"Caregiver contact email: {resident['caregiver_contact'].get('email')}")
    decision = handle_call_result(resident, ESCALATION_CALL_RESULT)
    print(f"\nDecision: escalate={decision['escalate']}")
    print(f"concern_summary: {decision['concern_summary']!r}")


if __name__ == "__main__":
    main()
