"""
Vera's call orchestration agent, built on the AWS Strands Agents SDK.

This wires place_social_checkin_call and place_activity_call up as Strands
tools on an Agent. Note: driving the Agent with natural-language prompts
requires a configured model provider (Strands defaults to Amazon Bedrock,
which needs AWS credentials) - that hasn't been set up in this project yet.
The tool functions themselves work standalone without any model provider,
which is how run_test_call.py below exercises them.
"""

from strands import Agent

from tools import place_social_checkin_call, place_activity_call

SYSTEM_PROMPT = (
    "You are Vera's call orchestration assistant. You place two kinds of "
    "calls to residents through CALL-E: social check-in calls "
    "(place_social_checkin_call) and daily activity/motivation calls "
    "(place_activity_call). Only place a call when a resident_id is clearly "
    "given or confirmed - never guess which resident to call."
)


def build_agent() -> Agent:
    return Agent(
        tools=[place_social_checkin_call, place_activity_call],
        system_prompt=SYSTEM_PROMPT,
    )


if __name__ == "__main__":
    agent = build_agent()
    # Example natural-language usage (needs a model provider configured):
    # agent("Place a social check-in call to resident_1")
    print("Agent built with tools:", agent.tool_names)
