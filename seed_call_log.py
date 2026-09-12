"""
One-time seed script: populates call_log.json with realistic demo entries
(no real calls placed) so the local dashboard has call history to show
before any real scheduled calls have run. Safe to re-run - it overwrites
call_log.json from scratch each time.
"""

import datetime

import call_log
import data_source

NOW = datetime.datetime.now(datetime.UTC)


def _hours_ago(hours: float) -> str:
    return (NOW - datetime.timedelta(hours=hours)).isoformat()


def _make_structured(*, run_id: str, status: str, summary: str, transcript: str, duration_seconds: int) -> dict:
    return {
        "run_id": run_id,
        "status": status,
        "result": {
            "post_summary": summary,
            "transcript": transcript,
            "extracted": {"calling": {"duration_seconds": duration_seconds}},
        },
    }


def _routine(reasoning: str) -> dict:
    return {"escalate": False, "reasoning": reasoning, "concern_summary": ""}


def _escalated(reasoning: str, concern_summary: str) -> dict:
    return {"escalate": True, "reasoning": reasoning, "concern_summary": concern_summary}


def main() -> None:
    call_log.LOG_PATH.unlink(missing_ok=True)

    evelyn = data_source.get_resident("resident_1")
    walter = data_source.get_resident("resident_2")
    irene = data_source.get_resident("resident_3")

    entries = [
        # Evelyn - routine social check-in
        (
            evelyn,
            "social_checkin",
            _make_structured(
                run_id="demo-evelyn-checkin-routine",
                status="COMPLETED",
                summary=(
                    "Evelyn had a cheerful, engaged conversation. She watched Family Feud and "
                    "Wheel of Fortune today, mentioned her arthritis was a little achy this "
                    "morning like usual, and talked fondly about Shalyn's upcoming wedding."
                ),
                transcript=(
                    "[00:00:00] BOT: Hi Evelyn, this is Vera calling to check in!\n"
                    "[00:00:04] USER: Oh hi there, sweetie.\n"
                    "[00:00:08] BOT: How's your day going?\n"
                    "[00:00:12] USER: Oh it's good, just watched Wheel of Fortune. My hands are "
                    "a little achy today like always but I'm doing fine.\n"
                    "[00:00:22] BOT: I'm glad you're doing well! Anything exciting coming up?\n"
                    "[00:00:28] USER: Shalyn's wedding! I keep thinking about it, so exciting.\n"
                    "[00:00:40] USER: No, I'm just happy today. Talk soon, dear.\n"
                ),
                duration_seconds=142,
            ),
            _routine(
                "Achy hands are explicitly normal per Evelyn's criteria (arthritis). No fall, "
                "chest pain, breathing difficulty, or confusion mentioned. Cheerful and lucid "
                "throughout - routine call."
            ),
            _hours_ago(20),
        ),
        # Evelyn - escalated social check-in (the fall scenario)
        (
            evelyn,
            "social_checkin",
            _make_structured(
                run_id="demo-evelyn-checkin-escalation",
                status="COMPLETED",
                summary=(
                    "Evelyn mentioned tripping and falling near the kitchen this morning. She "
                    "said she is okay but sounded a bit shaken during the call."
                ),
                transcript=(
                    "[00:00:00] BOT: Hi Evelyn, this is Vera calling to check in!\n"
                    "[00:00:04] USER: Oh, hi. I'm okay I think, just a little shaken up.\n"
                    "[00:00:09] BOT: Oh no, what happened?\n"
                    "[00:00:12] USER: I tripped by the kitchen this morning and fell, but I "
                    "think I'm okay, just sore.\n"
                    "[00:00:20] BOT: I'm really glad you're talking to me. Is James with you "
                    "right now?\n"
                    "[00:00:25] USER: He's here, he helped me up. I just felt a little dizzy "
                    "for a minute after.\n"
                ),
                duration_seconds=98,
            ),
            _escalated(
                "Evelyn's criteria explicitly state to call immediately if she mentions a "
                "fall. She clearly reported falling near the kitchen and feeling dizzy "
                "afterward.",
                "Evelyn reported falling near the kitchen this morning. She says she's okay "
                "but sounded shaken, mentioned soreness, and felt dizzy briefly after the "
                "fall. James was present and helped her up.",
            ),
            _hours_ago(44),
        ),
        # Evelyn - routine activity call
        (
            evelyn,
            "activity",
            _make_structured(
                run_id="demo-evelyn-activity-routine",
                status="COMPLETED",
                summary=(
                    "Evelyn completed the seated stepper machine routine and cool-down "
                    "stretches without any trouble, chatting about her granddaughter Destiny's "
                    "upcoming basketball season."
                ),
                transcript=(
                    "[00:00:00] BOT: Hi Evelyn, ready for a bit of movement today?\n"
                    "[00:00:05] USER: Sure thing, let's do it.\n"
                    "[00:00:10] USER: That stepper machine always wakes me up a little.\n"
                    "[00:00:20] BOT: How did that feel?\n"
                    "[00:00:24] USER: Good! No trouble today.\n"
                ),
                duration_seconds=210,
            ),
            _routine("No concerning content; activity completed without difficulty."),
            _hours_ago(4),
        ),
        # Walter - routine social check-in
        (
            walter,
            "social_checkin",
            _make_structured(
                run_id="demo-walter-checkin-routine",
                status="COMPLETED",
                summary=(
                    "Walter talked about old jazz records and a boat he used to work on. "
                    "Mood seemed good overall."
                ),
                transcript=(
                    "[00:00:00] BOT: Hi Walter, this is Vera calling to check in.\n"
                    "[00:00:05] USER: Oh hey. Just listening to some records.\n"
                    "[00:00:15] USER: Miles Davis today. Can't beat it.\n"
                ),
                duration_seconds=131,
            ),
            _routine("Placeholder criteria; nothing concerning mentioned in the call."),
            _hours_ago(30),
        ),
        # Walter - routine activity call
        (
            walter,
            "activity",
            _make_structured(
                run_id="demo-walter-activity-routine",
                status="COMPLETED",
                summary="Walter did his seated arm and shoulder circles with the nurse present.",
                transcript=(
                    "[00:00:00] BOT: Hi Walter, time for some arm circles today.\n"
                    "[00:00:06] USER: Alright, let's get it over with.\n"
                    "[00:00:30] USER: Done. That wasn't so bad.\n"
                ),
                duration_seconds=95,
            ),
            _routine("Placeholder criteria; activity completed, no concerns."),
            _hours_ago(8),
        ),
        # Irene - routine social check-in
        (
            irene,
            "social_checkin",
            _make_structured(
                run_id="demo-irene-checkin-routine",
                status="COMPLETED",
                summary="Irene talked about baking pan dulce this weekend and her cat Pepito.",
                transcript=(
                    "[00:00:00] BOT: Hi Irene, this is Vera calling to check in!\n"
                    "[00:00:05] USER: Hola! I'm baking today.\n"
                    "[00:00:15] USER: Pepito is right here supervising, of course.\n"
                ),
                duration_seconds=118,
            ),
            _routine("Placeholder criteria; cheerful call, nothing concerning."),
            _hours_ago(26),
        ),
        # Irene - rest-day light activity call
        (
            irene,
            "activity",
            _make_structured(
                run_id="demo-irene-activity-restday",
                status="COMPLETED",
                summary="Rest day - light check-in only, no exercise encouragement. Irene was doing fine.",
                transcript=(
                    "[00:00:00] BOT: Hi Irene, just a low-key check-in today, no exercise talk!\n"
                    "[00:00:06] USER: Oh good, I'm resting today anyway.\n"
                ),
                duration_seconds=64,
            ),
            _routine("Rest day light check-in; nothing concerning."),
            _hours_ago(2),
        ),
    ]

    for resident, call_type, structured, decision, timestamp in entries:
        call_log.append_call(resident=resident, call_type=call_type, call_result=structured, escalation_decision=decision)
        # append_call stamps "now" - overwrite with our staggered demo timestamp instead.
        logged = call_log._load()
        logged[-1]["timestamp"] = timestamp
        call_log._save(logged)

    print(f"Seeded {len(entries)} demo call log entries into {call_log.LOG_PATH}")


if __name__ == "__main__":
    main()
