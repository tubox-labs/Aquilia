"""Commit Agent — generates commit messages and executes git commits.

Follows the structured commit message format:
[type] short summary

Files:
- file1.py

Reason:
Explanation
"""

from __future__ import annotations

import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .base import AgentType, BaseAgent, Message, MessageType
from ..state import SwarmState, TaskRecord


class CommitAgent(BaseAgent):
    """Executes git commits with structured messages."""

    agent_type = AgentType.COMMIT
    REPO_ROOT: Path = Path(__file__).resolve().parent.parent.parent

    def _handle_message(self, msg: Message) -> None:
        if msg.msg_type == MessageType.COMMIT_REQUEST:
            commit_type = msg.payload.get("type", "feat")
            summary = msg.payload.get("summary", "")
            files = msg.payload.get("files", [])
            reason = msg.payload.get("reason", "")
            task_id = msg.payload.get("task_id", "")

            success, commit_hash = self._execute_commit(commit_type, summary, files, reason, task_id)

            response = Message(
                msg_id=str(uuid.uuid4()),
                msg_type=MessageType.COMMIT_CONFIRMED if success else MessageType.TASK_FAILED,
                sender_id=self.agent_id,
                recipient_id=msg.sender_id,
                payload={
                    "success": success,
                    "commit_hash": commit_hash,
                    "task_id": task_id,
                    "error": "" if success else "Commit failed",
                },
                correlation_id=msg.msg_id,
            )
            self.send_message(response)

    def _execute_commit(
        self,
        commit_type: str,
        summary: str,
        files: list[str],
        reason: str,
        task_id: str,
    ) -> tuple[bool, str]:
        file_list = "\n".join(f"- {f}" for f in files)
        message = f"[{commit_type}] {summary}\n\nFiles:\n{file_list}\n\nReason:\n{reason}"

        try:
            subprocess.run(
                ["git", "add"] + files,
                capture_output=True,
                text=True,
                check=True,
                cwd=self.REPO_ROOT,
            )

            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.REPO_ROOT,
            )

            commit_hash = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
                cwd=self.REPO_ROOT,
            ).stdout.strip()

            self._state.commit_count += 1
            return True, commit_hash

        except subprocess.CalledProcessError as e:
            return False, f"Subprocess error: {e}"

    async def run(self) -> None:
        self.register_in_state()
        self.process_messages()