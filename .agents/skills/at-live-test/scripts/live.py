#!/usr/bin/env python3
"""
Exercise the `at` integration on the running development instance.

Reuses the authentication and transport of ``script/ha`` (``script/.lib/ha_cli``), so the
development token is read from disk and never printed.

Usage:
    mise exec -- python .agents/skills/at-live-test/scripts/live.py preview "turn on the bed light at seven thirty"
    mise exec -- python .agents/skills/at-live-test/scripts/live.py say "in forty five minutes turn off the lights"
    mise exec -- python .agents/skills/at-live-test/scripts/live.py say --keep "at 11pm run the bedtime script"
    mise exec -- python .agents/skills/at-live-test/scripts/live.py jobs

Exit codes follow ``script/ha``: 0 success, 1 failed, 2 unreachable, 3 auth failed.
"""

import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
from typing import Any

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "script" / ".lib"))
os.chdir(REPO)

from ha_cli.client import DEFAULT_URL, HaClient, HaError, read_token  # noqa: E402 - needs the path above

DOMAIN = "at"


async def _pending(client: HaClient) -> list[dict[str, Any]]:
    result = await client.rest(
        "POST", f"/api/services/{DOMAIN}/list", payload={"status": ["pending"]}, params={"return_response": ""}
    )
    return result["service_response"]["pending"]


def _out(line: str) -> None:
    sys.stdout.write(f"{line}\n")


def _job_line(job: dict[str, Any]) -> str:
    return f"{job['id']}  due {job['due']}  {job['summary']}"


async def cmd_preview(client: HaClient, args: argparse.Namespace) -> int:
    """Dry-run typed text through the panel's preview: parsed, checked, never saved."""
    result = await client.ws(f"{DOMAIN}/parse", text=args.text)
    _out(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


async def cmd_say(client: HaClient, args: argparse.Namespace) -> int:
    """Send a sentence through Assist, report the jobs it created, and cancel them unless --keep."""
    before = {job["id"] for job in await _pending(client)}
    result = await client.rest(
        "POST",
        "/api/services/conversation/process",
        payload={"text": args.text, "language": args.language},
        params={"return_response": ""},
    )
    response = result["service_response"]["response"]
    _out(f"speech: {response['speech'].get('plain', {}).get('speech', '')}")
    _out(f"type:   {response.get('response_type')}")
    created = [job for job in await _pending(client) if job["id"] not in before]
    for job in created:
        _out(f"job:    {_job_line(job)}")
    if not created:
        _out("job:    none created")
    if not args.keep:
        for job in created:
            await client.rest("POST", f"/api/services/{DOMAIN}/cancel", payload={"job_id": job["id"]})
            _out(f"cancelled {job['id']}")
    return 0


async def cmd_jobs(client: HaClient, _args: argparse.Namespace) -> int:
    """List pending jobs."""
    jobs = await _pending(client)
    for job in jobs:
        _out(_job_line(job))
    if not jobs:
        _out("no pending jobs")
    return 0


def main() -> int:
    """Parse the arguments and run one command."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default=os.environ.get("HA_URL", DEFAULT_URL))
    parser.add_argument("--timeout", type=float, default=30)
    commands = parser.add_subparsers(dest="command", required=True)
    preview = commands.add_parser("preview", help="dry-run typed text; nothing is saved")
    preview.add_argument("text")
    say = commands.add_parser("say", help="send a sentence through Assist; cancels what it creates")
    say.add_argument("text")
    say.add_argument("--language", default="en")
    say.add_argument("--keep", action="store_true", help="leave the created job pending")
    commands.add_parser("jobs", help="list pending jobs")
    args = parser.parse_args()
    handler = {"preview": cmd_preview, "say": cmd_say, "jobs": cmd_jobs}[args.command]

    async def run() -> int:
        async with HaClient(args.url, read_token(), args.timeout) as client:
            return await handler(client, args)

    try:
        return asyncio.run(run())
    except HaError as err:
        sys.stderr.write(f"error: {err}\n")
        return err.code


if __name__ == "__main__":
    sys.exit(main())
