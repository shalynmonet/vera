"""
Thin wrapper around the `calle` CLI (CALL-E's phone-calling service).

Design note: CALL-E's MCP server (`calle mcp config`) is a remote HTTP
endpoint that expects an OAuth bearer token. The `calle` CLI already holds
that token in its own local credential cache (~/.calle-mcp) and manages
login/refresh for it. Rather than extracting that token into this project
(duplicating a live credential across two codebases, which is exactly what
CALL-E's own skill instructions and general credential hygiene advise
against), this module shells out to the `calle` CLI itself for every call -
the same way it's driven interactively - so the token never leaves its own
credential store. Run `calle auth login` once outside this project before
using these functions.
"""

import json
import os
import shutil
import subprocess
from typing import Any

# Lambda layer path: our layer places node at layer-root/bin/node (which
# Lambda automatically adds to PATH as /opt/bin) and the calle package
# under layer-root/calle/node_modules/@call-e/cli - but there's no `calle`
# shim on PATH there, only the raw entry-point script, so it must be run
# as `node <path-to-calle.js>` rather than invoked by name.
_LAMBDA_CALLE_JS = "/opt/calle/node_modules/@call-e/cli/bin/calle.js"


def _resolve_calle_command() -> list[str]:
    calle_exe = shutil.which("calle")
    if calle_exe:
        return [calle_exe]
    if os.path.exists(_LAMBDA_CALLE_JS):
        node_exe = shutil.which("node") or "/opt/bin/node"
        return [node_exe, _LAMBDA_CALLE_JS]
    raise CalleError(
        "Could not find the `calle` CLI (checked PATH and the Lambda layer "
        f"path {_LAMBDA_CALLE_JS}). Locally: `npm install -g @call-e/cli` "
        "and `calle auth login`. In Lambda: check the vera-calle-nodejs "
        "layer is attached."
    )


CALLE_ENV = {
    **os.environ,
    "CALLE_SOURCE": "skills_sh",
    "CALLE_INTEGRATION": "skills_sh_skill",
    "CALLE_INTEGRATION_VERSION": "0.1.0",
}


class CalleError(RuntimeError):
    """Raised when the calle CLI fails or returns something unexpected."""


class CalleAuthError(CalleError):
    """Raised when calle reports auth_required. Run `calle auth login`."""


def _run(args: list[str], timeout: int = 180) -> dict[str, Any]:
    calle_command = _resolve_calle_command()
    # CALLE_CACHE_ROOT is unset in local dev (calle uses its own default,
    # ~/.calle-mcp). bootstrap.py sets it to /tmp/calle-cache in Lambda,
    # where that's the only writable directory and there's no real HOME.
    cache_root = os.environ.get("CALLE_CACHE_ROOT")
    if cache_root:
        args = [*args, "--cache-root", cache_root]
    result = subprocess.run(
        [*calle_command, *args, "--json"],
        capture_output=True,
        text=True,
        env=CALLE_ENV,
        timeout=timeout,
        shell=False,
    )
    stdout = result.stdout.strip()
    if not stdout:
        raise CalleError(f"calle {' '.join(args)} produced no output: {result.stderr.strip()}")
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise CalleError(f"calle {' '.join(args)} returned non-JSON output: {stdout!r}") from exc

    error = payload.get("error")
    if isinstance(error, dict) and error.get("code") == "auth_required":
        raise CalleAuthError("CALL-E session expired. Run `calle auth login` and try again.")
    return payload


def auth_status() -> dict[str, Any]:
    return _run(["auth", "status"])


def plan_call(to_phone: str, goal: str, language: str | None = None, region: str | None = None) -> dict[str, Any]:
    """Planning-only call via plan_call. Does not place a call."""
    args = ["call", "plan", "--to-phone", to_phone, "--goal", goal]
    if language:
        args += ["--language", language]
    if region:
        args += ["--region", region]
    return _run(args, timeout=170)


def start_call(to_phone: str, goal: str, language: str | None = None, region: str | None = None) -> dict[str, Any]:
    """Plans and places a real outbound call via run_call. This is a real phone call."""
    args = ["call", "start", "--to-phone", to_phone, "--goal", goal]
    if language:
        args += ["--language", language]
    if region:
        args += ["--region", region]
    return _run(args, timeout=170)


def get_call_status(run_id: str) -> dict[str, Any]:
    return _run(["call", "status", "--run-id", run_id])


def extract_structured_content(payload: dict[str, Any]) -> dict[str, Any]:
    """Pull the structuredContent block out of a calle CLI JSON response,
    whether it came from `call start` (status_result) or `call status` (result).
    """
    for key in ("status_result", "result"):
        block = payload.get(key)
        if isinstance(block, dict):
            structured = block.get("structuredContent")
            if isinstance(structured, dict):
                return structured
    raise CalleError(f"Could not find structuredContent in calle response: {payload!r}")
