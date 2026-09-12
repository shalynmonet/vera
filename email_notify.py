"""
Resend email integration for escalation alerts. Uses urllib (stdlib) rather
than the `requests` package, since `requests` is only pulled in by
strands-agents-tools (which isn't in the Lambda layer) - this way there's
no extra dependency to package for either environment.

Requires a `vera/resend-api-key` secret in Secrets Manager (see secrets.py).
Sends from vera@sha-i.com (verified in Resend); override via the
RESEND_FROM_ADDRESS env var if that ever changes.
"""

import json
import os
import urllib.error
import urllib.request

import secrets as secrets_helper

RESEND_API_URL = "https://api.resend.com/emails"
RESEND_SECRET_NAME = os.environ.get("RESEND_API_KEY_SECRET_NAME", "vera/resend-api-key")
RESEND_FROM_ADDRESS = os.environ.get("RESEND_FROM_ADDRESS", "Vera <vera@sha-i.com>")


class EmailSendError(RuntimeError):
    pass


def send_escalation_email(*, to_email: str, subject: str, body_text: str) -> dict:
    api_key = secrets_helper.get_secret_string(RESEND_SECRET_NAME)

    payload = json.dumps(
        {
            "from": RESEND_FROM_ADDRESS,
            "to": [to_email],
            "subject": subject,
            "text": body_text,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        RESEND_API_URL,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            # Resend's API is Cloudflare-fronted; the default urllib User-Agent
            # gets blocked at the edge (HTTP 403, Cloudflare error code 1010)
            # before it even reaches Resend's application layer.
            "User-Agent": "vera-call-orchestrator/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise EmailSendError(f"Resend API returned {exc.code}: {error_body}") from exc
