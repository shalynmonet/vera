"""
Lambda cold-start bootstrap: reconstructs calle's local token cache in /tmp
from a secret in AWS Secrets Manager, so the calle CLI (invoked via
subprocess from calle_cli.py, same as local dev) finds valid cached
credentials. Lambda's only writable directory is /tmp, and there's no real
$HOME the way there is on a dev machine.

The secret's value must be the *exact* JSON content of a real
`calle auth login` token.json file, uploaded byte-for-byte via:

    aws secretsmanager create-secret --name vera/calle-token \
        --secret-string file://path/to/token.json

Never hand-construct or paraphrase this JSON - its full schema (every field
calle actually writes) was deliberately never inspected in this project;
uploading the real file as-is avoids needing to know it.
"""

import hashlib
import json
import os
from pathlib import Path

import boto3

CACHE_ROOT = "/tmp/calle-cache"
# Matches calle's default `<base-url>/mcp/<channel>` server URL exactly.
SERVER_URL = "https://seleven-mcp-sg.airudder.com/mcp/openagent_oauth"
SECRET_NAME = os.environ.get("CALLE_TOKEN_SECRET_NAME", "vera/calle-token")

_bootstrapped = False


def _server_hash(server_url: str) -> str:
    # Matches @call-e/core lib/cache.js: serverHash() = md5(serverUrl) hex.
    return hashlib.md5(server_url.encode("utf-8")).hexdigest()


def ensure_token_cache() -> None:
    """Idempotent per warm Lambda execution environment (/tmp persists
    across warm invocations, so this only hits Secrets Manager once per
    cold start). Sets CALLE_CACHE_ROOT so calle_cli.py passes
    --cache-root on every calle CLI invocation.
    """
    global _bootstrapped
    token_path = Path(CACHE_ROOT) / _server_hash(SERVER_URL) / "token.json"

    os.environ["CALLE_CACHE_ROOT"] = CACHE_ROOT
    if _bootstrapped and token_path.exists():
        return

    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=SECRET_NAME)
    secret_value = response["SecretString"]

    # Validate it's JSON without inspecting/logging its contents further.
    json.loads(secret_value)

    token_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(token_path.parent, 0o700)
    token_path.write_text(secret_value, encoding="utf-8")
    os.chmod(token_path, 0o600)

    _bootstrapped = True
