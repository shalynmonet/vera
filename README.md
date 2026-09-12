# Vera

An AI-powered wellness check-in phone service for elderly family members and care recipients, built on the [AWS Strands Agents SDK](https://strandsagents.com) and [CALL-E](https://skills.sh/calle-ai/call-e-integrations) for placing real outbound phone calls.

Vera places two kinds of calls to each resident:
- **Social Check-In** - an open-ended, warm conversation, no fixed script
- **Activity** - a gentle nudge toward that day's scheduled activity (with a lighter, exercise-free version on rest days)

After each call, an LLM-based escalation step (via Amazon Bedrock) judges the result against that specific resident's own plain-language emergency criteria - written by their real family or caregiver, not a fixed keyword list - and sends an urgent email via Resend if it warrants immediate attention.

## Architecture

```
tools.py               Strands tools: place_social_checkin_call, place_activity_call
calle_cli.py            Wraps the `calle` CLI (subprocess) rather than a raw MCP client,
                        so CALL-E's OAuth token never leaves its own credential store
templates.py            Goal-text templates for each call type
escalation.py           evaluate_call_for_escalation - Bedrock-backed judgment call
email_notify.py         Resend integration for escalation alerts
call_log.py             Local call-history log (call_log.json)
data_source.py          Single swappable seam between mock data and a real backend
agent.py                Strands Agent wiring (tools registered; LLM-driven invocation
                        needs a configured model provider, not required to use the
                        tools directly)
bootstrap.py            Lambda cold-start: reconstructs calle's token cache in /tmp
                        from an AWS Secrets Manager secret
lambda_handler.py       Lambda entry point
dashboard.html          Local, dependency-free demo dashboard (residents + call history)
aws/                    IAM policies, Lambda layer/function build scripts, EventBridge
                        Scheduler setup
```

Deployed on AWS Lambda behind two layers (Node.js + `@call-e/cli`, and `strands-agents`), with EventBridge Scheduler driving recurring calls and Secrets Manager holding the CALL-E token - no long-lived credentials on disk in the deployed environment.

## Setup

**Prerequisites:** Python 3.12+, Node.js 22+ with `npm`, an AWS account (for the escalation/Lambda pieces).

```bash
python -m venv .venv
.venv/Scripts/pip install strands-agents strands-agents-tools   # Windows
# .venv/bin/pip install strands-agents strands-agents-tools     # macOS/Linux

npm install -g @call-e/cli
calle auth login   # browser-based OAuth; see https://skills.sh/calle-ai/call-e-integrations
```

Copy the example resident data (the real file is gitignored - it's meant to hold real personal information about real people you're setting this up for):

```bash
cp mock_residents.example.json mock_residents.json
```

Generate demo call history for the dashboard:

```bash
python seed_call_log.py
```

Run the local dashboard (must be served, not opened via `file://`, or the JSON fetches silently fail):

```bash
python -m http.server 8420
# open http://localhost:8420/dashboard.html
```

### Placing a real call

```bash
python run_test_call.py resident_1
```

**This places a real outbound phone call.** `place_social_checkin_call` and `place_activity_call` in `tools.py` are the two entry points.

### Escalation + email (optional, needs AWS)

Requires Bedrock model access in your AWS account and a Resend API key in Secrets Manager:

```bash
aws secretsmanager create-secret --name vera/resend-api-key --secret-string "YOUR_KEY"
python test_escalation.py   # judgment-call only, no email sent
python test_email.py        # full path, sends a real email
```

### AWS deployment

See `aws/` for the Lambda layer build scripts, IAM policy documents, and `create_schedules.py` for the EventBridge Scheduler setup. All scripts use `vera-*` resource naming throughout so IAM policies can stay scoped rather than using broad/admin access.

## License

MIT - see [LICENSE](LICENSE).
