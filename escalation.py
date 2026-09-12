"""
Escalation evaluation: after a call completes, judge whether its result
meets *this resident's own* plain-language emergency criteria closely
enough to alert their caregiver immediately.

Deliberately uses LLM reasoning (via a Bedrock-backed Strands Agent) rather
than keyword matching - criteria differ per resident and are meant to be
human judgment calls in the caregiver's own words, not a fixed keyword list.

BEDROCK_MODEL_ID below is a placeholder - confirm the actual available
model ID in your account/region (`aws bedrock list-foundation-models`)
before running this for real, once Bedrock access is set up.
"""

import os
from typing import Any

from pydantic import BaseModel, Field
from strands import Agent, tool
from strands.models.bedrock import BedrockModel

import email_notify

BEDROCK_MODEL_ID = os.environ.get("VERA_BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-5-20250929-v1:0")
BEDROCK_REGION = os.environ.get("AWS_REGION", "us-east-1")

SYSTEM_PROMPT = (
    "You are a careful, conservative safety reviewer for an elder-companion phone-call "
    "service. You are given one completed call's result and a specific resident's own "
    "plain-language emergency criteria, written by their real family or caregiver. "
    "Decide whether this call result meets THIS resident's stated criteria closely "
    "enough to warrant an immediate caregiver alert, or whether it is routine.\n\n"
    "Rules:\n"
    "- Judge only against what the criteria and the transcript/summary actually say. "
    "Do not invent concerns that aren't supported by the call content.\n"
    "- Do not escalate for things the resident's own criteria explicitly describe as "
    "normal for them (e.g. a condition they already live with).\n"
    "- When genuinely uncertain whether something crosses the line, err toward "
    "escalating - a missed real concern is worse than an unnecessary alert.\n"
    "- concern_summary should be short (1-3 sentences) and specific enough to be useful "
    "in an urgent email to a caregiver who wasn't on the call. Leave it empty if not "
    "escalating."
)


class EscalationDecision(BaseModel):
    escalate: bool = Field(
        description="True if this call result meets the resident's emergency criteria and needs immediate caregiver attention."
    )
    reasoning: str = Field(
        description="Brief explanation of the judgment, referencing the specific criteria and what in the call did or didn't meet it."
    )
    concern_summary: str = Field(
        default="",
        description="If escalating: a short, specific summary of the concern for an urgent caregiver email. Empty string if not escalating.",
    )


_escalation_agent: Agent | None = None


def _get_escalation_agent() -> Agent:
    global _escalation_agent
    if _escalation_agent is None:
        model = BedrockModel(model_id=BEDROCK_MODEL_ID, region_name=BEDROCK_REGION)
        _escalation_agent = Agent(model=model, system_prompt=SYSTEM_PROMPT)
    return _escalation_agent


@tool
def evaluate_call_for_escalation(call_result: dict[str, Any], resident: dict[str, Any]) -> dict[str, Any]:
    """Judge whether a completed CALL-E call result warrants immediate
    caregiver escalation, using the resident's own plain-language
    emergency_criteria rather than hardcoded keyword matching.

    Returns {"escalate": bool, "reasoning": str, "concern_summary": str}.
    """
    result_block = call_result.get("result") or {}
    summary = result_block.get("post_summary") or result_block.get("summary") or "n/a"
    transcript = result_block.get("transcript") or "n/a"
    status = call_result.get("status", "n/a")
    emergency_criteria = resident.get("emergency_criteria", "").strip()

    if not emergency_criteria:
        return EscalationDecision(
            escalate=False,
            reasoning="No emergency_criteria configured for this resident; skipping evaluation.",
        ).model_dump()

    prompt = (
        f"Resident: {resident.get('name', 'unknown')}\n"
        f"Resident's own emergency criteria (from their family/caregiver): {emergency_criteria}\n\n"
        f"Call status: {status}\n"
        f"Call summary: {summary}\n\n"
        f"Full transcript:\n{transcript}\n\n"
        "Decide whether this call result meets this resident's emergency criteria."
    )
    decision = _get_escalation_agent().structured_output(EscalationDecision, prompt)
    return decision.model_dump()


def handle_call_result(resident: dict[str, Any], call_result: dict[str, Any]) -> dict[str, Any]:
    """Evaluate a completed call and send an escalation email if warranted.
    Always returns the decision dict, for logging alongside the call result.
    """
    decision = evaluate_call_for_escalation(call_result=call_result, resident=resident)
    if decision["escalate"]:
        _send_escalation_alert(resident, decision, call_result)
    return decision


def _send_escalation_alert(resident: dict[str, Any], decision: dict[str, Any], call_result: dict[str, Any]) -> None:
    caregiver = resident.get("caregiver_contact") or {}
    to_email = caregiver.get("email")
    if not to_email:
        print(
            f"WARNING: escalation triggered for {resident.get('name')} but caregiver_contact "
            "has no email on file; alert NOT sent."
        )
        return

    transcript = (call_result.get("result") or {}).get("transcript") or ""
    excerpt = transcript[-800:] if len(transcript) > 800 else transcript

    subject = f"⚠️ Vera flagged something during {resident.get('name')}'s call"
    body = (
        f"Vera's automated review flagged this call from {resident.get('name')}'s check-in "
        "as needing your attention.\n\n"
        f"Concern: {decision['concern_summary']}\n\n"
        f"Reasoning: {decision['reasoning']}\n\n"
        f"Call status: {call_result.get('status')}\n\n"
        f"Transcript excerpt:\n{excerpt}\n\n"
        "This is an automated alert based on the call content - please check in with "
        "them directly to confirm."
    )

    email_notify.send_escalation_email(to_email=to_email, subject=subject, body_text=body)
    print(f"Escalation email sent to {to_email} for {resident.get('name')}.")
