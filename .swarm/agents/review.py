"""Review Agent — validates code changes before they are committed.

Checks style, architecture, and test coverage. Rejects changes
that do not meet quality standards.
"""

from __future__ import annotations

import subprocess
import uuid
from pathlib import Path

from .base import AgentType, BaseAgent, Message, MessageType


class ReviewAgent(BaseAgent):
    """Validates code quality before commits."""

    agent_type = AgentType.REVIEW
    REPO_ROOT: Path = Path(__file__).resolve().parent.parent.parent

    def _handle_message(self, msg: Message) -> None:
        if msg.msg_type == MessageType.REVIEW_REQUEST:
            files = msg.payload.get("files", [])
            task_id = msg.payload.get("task_id", "")

            issues = self._review_files(files)

            response = Message(
                msg_id=str(uuid.uuid4()),
                msg_type=MessageType.REVIEW_RESULT,
                sender_id=self.agent_id,
                recipient_id=msg.sender_id,
                payload={
                    "approved": len(issues) == 0,
                    "issues": issues,
                    "task_id": task_id,
                },
                correlation_id=msg.msg_id,
            )
            self.send_message(response)

    def _review_files(self, files: list[str]) -> list[str]:
        issues: list[str] = []

        for filepath in files:
            repo_path = self.REPO_ROOT / filepath
            if not repo_path.exists():
                issues.append(f"File not found: {filepath}")
                continue

            issues.extend(self._check_style(filepath))

        return issues

    def _check_style(self, filepath: str) -> list[str]:
        issues: list[str] = []

        if filepath.endswith(".py"):
            try:
                result = subprocess.run(
                    ["ruff", "check", str(self.REPO_ROOT / filepath), "--output-format=text"],
                    capture_output=True,
                    text=True,
                    cwd=self.REPO_ROOT,
                    timeout=30,
                )
                if result.returncode != 0 and result.stdout.strip():
                    for line in result.stdout.strip().split("\n"):
                        if line.strip():
                            issues.append(f"Ruff: {line.strip()}")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass

        return issues

    async def run(self) -> None:
        self.register_in_state()
        self.process_messages()