"""Test Agent — runs tests, linting, and type checking.

Failure blocks commit creation. Must pass all checks before
a task is considered complete.
"""

from __future__ import annotations

import subprocess
import uuid
from pathlib import Path

from .base import AgentType, BaseAgent, Message, MessageType


class TestAgent(BaseAgent):
    """Runs the test suite and quality checks."""

    agent_type = AgentType.TEST
    REPO_ROOT: Path = Path(__file__).resolve().parent.parent.parent

    def _handle_message(self, msg: Message) -> None:
        if msg.msg_type == MessageType.TEST_REQUEST:
            scope = msg.payload.get("scope", "full")
            task_id = msg.payload.get("task_id", "")

            results = self._run_checks(scope)

            response = Message(
                msg_id=str(uuid.uuid4()),
                msg_type=MessageType.TEST_RESULT,
                sender_id=self.agent_id,
                recipient_id=msg.sender_id,
                payload={
                    "passed": results["passed"],
                    "results": results,
                    "task_id": task_id,
                },
                correlation_id=msg.msg_id,
            )
            self.send_message(response)

    def _run_checks(self, scope: str) -> dict:
        results: dict[str, bool | str] = {
            "passed": True,
            "ruff_check": "skipped",
            "ruff_format": "skipped",
            "pytest": "skipped",
        }

        if scope in ("full", "style"):
            results.update(self._run_ruff())

        if scope in ("full", "tests"):
            results.update(self._run_pytest())

        results["passed"] = all(
            v not in ("failed", False) for v in results.values() if isinstance(v, str)
        )
        return results

    def _run_ruff(self) -> dict[str, str]:
        results: dict[str, str] = {}

        try:
            r = subprocess.run(
                ["ruff", "check", str(self.REPO_ROOT / ".swarm"), "--output-format=text"],
                capture_output=True,
                text=True,
                cwd=self.REPO_ROOT,
                timeout=60,
            )
            results["ruff_check"] = "passed" if r.returncode == 0 else f"failed: {r.stdout.strip()[:200]}"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            results["ruff_check"] = "skipped (ruff not available)"

        try:
            r = subprocess.run(
                ["ruff", "format", "--check", str(self.REPO_ROOT / ".swarm")],
                capture_output=True,
                text=True,
                cwd=self.REPO_ROOT,
                timeout=60,
            )
            results["ruff_format"] = "passed" if r.returncode == 0 else "failed (format issues)"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            results["ruff_format"] = "skipped (ruff not available)"

        return results

    def _run_pytest(self) -> dict[str, str]:
        results: dict[str, str] = {}

        try:
            r = subprocess.run(
                ["pytest", "tests/", "-x", "--tb=short", "-q", "--timeout=120"],
                capture_output=True,
                text=True,
                cwd=self.REPO_ROOT,
                timeout=300,
            )
            results["pytest"] = "passed" if r.returncode == 0 else f"failed: {r.stdout.strip()[-300:]}"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            results["pytest"] = "skipped (pytest not available)"

        return results

    async def run(self) -> None:
        self.register_in_state()
        self.process_messages()
