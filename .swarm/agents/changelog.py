"""Change Log Agent — maintains CHANGES.md with append-only history.

After every commit, appends a structured entry. Never overwrites.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from .base import AgentType, BaseAgent, Message, MessageType


CHANGES_PATH: Path = Path(__file__).resolve().parent.parent.parent / "CHANGES.md"


class ChangeLogAgent(BaseAgent):
    """Append-only changelog writer."""

    agent_type = AgentType.CHANGELOG

    def _handle_message(self, msg: Message) -> None:
        if msg.msg_type == MessageType.CHANGELOG_UPDATE:
            commit_hash = msg.payload.get("commit_hash", "unknown")
            agent_id = msg.payload.get("agent_id", "unknown")
            files = msg.payload.get("files", [])
            summary = msg.payload.get("summary", "")

            self._append_entry(commit_hash, agent_id, files, summary)

            response = Message(
                msg_id=str(uuid.uuid4()),
                msg_type=MessageType.TASK_COMPLETE,
                sender_id=self.agent_id,
                recipient_id=msg.sender_id,
                payload={"status": "recorded"},
                correlation_id=msg.msg_id,
            )
            self.send_message(response)

    def _append_entry(
        self,
        commit_hash: str,
        agent_id: str,
        files: list[str],
        summary: str,
    ) -> None:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        entry = self._format_entry(commit_hash, timestamp, agent_id, files, summary)

        with open(CHANGES_PATH, "a") as f:
            f.write(entry)

    @staticmethod
    def _format_entry(
        commit_hash: str,
        timestamp: str,
        agent_id: str,
        files: list[str],
        summary: str,
    ) -> str:
        file_lines = "\n".join(f"- {f}" for f in files)
        lines = [
            "",
            f"## Commit {timestamp}",
            "",
            f"Timestamp: {timestamp}",
            "",
            f"Agent: {agent_id}",
            "",
            "Files Modified:",
            file_lines,
            "",
            "Summary:",
            summary,
            "",
            "Commit Hash:",
            commit_hash,
            "",
        ]
        return "\n".join(lines)

    async def run(self) -> None:
        self.register_in_state()
        self.process_messages()