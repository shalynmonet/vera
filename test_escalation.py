"""
Mock-scenario test for evaluate_call_for_escalation, against resident_1
(Evelyn)'s real emergency_criteria. Deliberately calls evaluate_call_for_
escalation directly (the judgment call only) rather than handle_call_result,
so this doesn't attempt to send any email - that's a separate step once the
Resend secret is set up.
"""

import data_source
from escalation import evaluate_call_for_escalation

ROUTINE_CALL_RESULT = {
    "status": "COMPLETED",
    "result": {
        "post_summary": (
            "Evelyn had a cheerful, engaged conversation. She watched Family Feud "
            "and Wheel of Fortune today, mentioned her arthritis was a little achy "
            "this morning like usual, and talked fondly about Shalyn's upcoming "
            "wedding."
        ),
        "transcript": (
            "[00:00:00] BOT: Hi Evelyn, this is Vera calling to check in!\n"
            "[00:00:04] USER: Oh hi there, sweetie.\n"
            "[00:00:08] BOT: How's your day going?\n"
            "[00:00:12] USER: Oh it's good, just watched Wheel of Fortune. My hands "
            "are a little achy today like always but I'm doing fine.\n"
            "[00:00:22] BOT: I'm glad you're doing well! Anything exciting coming up?\n"
            "[00:00:28] USER: Shalyn's wedding! I keep thinking about it, so exciting.\n"
            "[00:00:35] BOT: That's wonderful. Anything you'd like me to remember for "
            "next time?\n"
            "[00:00:40] USER: No, I'm just happy today. Talk soon, dear.\n"
        ),
    },
}

ESCALATION_CALL_RESULT = {
    "status": "COMPLETED",
    "result": {
        "post_summary": (
            "Evelyn mentioned tripping and falling near the kitchen this morning. "
            "She said she is okay but sounded a bit shaken during the call."
        ),
        "transcript": (
            "[00:00:00] BOT: Hi Evelyn, this is Vera calling to check in!\n"
            "[00:00:04] USER: Oh, hi. I'm okay I think, just a little shaken up.\n"
            "[00:00:09] BOT: Oh no, what happened?\n"
            "[00:00:12] USER: I tripped by the kitchen this morning and fell, but I "
            "think I'm okay, just sore.\n"
            "[00:00:20] BOT: I'm really glad you're talking to me. Is James with you "
            "right now?\n"
            "[00:00:25] USER: He's here, he helped me up. I just felt a little dizzy "
            "for a minute after.\n"
            "[00:00:32] BOT: I'm going to make sure someone checks in on you soon.\n"
        ),
    },
}


def main() -> None:
    resident = data_source.get_resident("resident_1")
    print(f"Testing against {resident['name']}'s emergency_criteria:")
    print(f"  {resident['emergency_criteria']}\n")

    for label, call_result in [("ROUTINE scenario", ROUTINE_CALL_RESULT), ("ESCALATION scenario", ESCALATION_CALL_RESULT)]:
        print(f"=== {label} ===")
        decision = evaluate_call_for_escalation(call_result=call_result, resident=resident)
        print(f"escalate: {decision['escalate']}")
        print(f"reasoning: {decision['reasoning']}")
        print(f"concern_summary: {decision['concern_summary']!r}")
        print()


if __name__ == "__main__":
    main()
