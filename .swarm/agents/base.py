"""Base agent classes and communication protocol for the swarm system.

Defines the abstract base for all agents, the message envelope format,
and the inter-agent communication protocol.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from ..state import (
    AgentRecord,
    SwarmState,
    TaskRecord,
    save_state,
    save_tasks,
)


class AgentType(str, Enum):
    PLANNER = "planner"
    COORDINATOR = "coordinator"
    WORKER = "worker"
    COMMIT = "commit"
    CHANGELOG = "changelog"
    REVIEW = "review"
    TEST = "test"


class MessageType(str, Enum):
    TASK_ASSIGNMENT = "task_assignment"
    TASK_COMPLETE = "task_complete"
    TASK_FAILED = "task_failed"
    COMMIT_REQUEST = "commit_request"
    COMMIT_CONFIRMED = "commit_confirmed"
    REVIEW_REQUEST = "review_request"
    REVIEW_RESULT = "review_result"
    TEST_REQUEST = "test_request"
    TEST_RESULT = "test_result"
    CHANGELOG_UPDATE = "changelog_update"
    CHECKPOINT_REQUEST = "checkpoint_request"
    RECOVERY_REQUEST = "recovery_request"
    STATUS_REPORT = "status_report"
    SPAWN_REQUEST = "spawn_request"
    SHUTDOWN = "shutdown"


@dataclass
class Message:
    """Inter-agent communication envelope."""

    msg_id: str
    msg_type: MessageType
    sender_id: str
    recipient_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    correlation_id: str | None = None

    def to_json(self) -> str:
        return json.dumps(
            {
                "msg_id": self.msg_id,
                "msg_type": self.msg_type.value,
                "sender_id": self.sender_id,
                "recipient_id": self.recipient_id,
                "payload": self.payload,
                "timestamp": self.timestamp,
                "correlation_id": self.correlation_id,
            }
        )

    @classmethod
    def from_json(cls, raw: str) -> Message:
        data = json.loads(raw)
        return cls(
            msg_id=data["msg_id"],
            msg_type=MessageType(data["msg_type"]),
            sender_id=data["sender_id"],
            recipient_id=data["recipient_id"],
            payload=data.get("payload", {}),
            timestamp=data.get("timestamp", ""),
            correlation_id=data.get("correlation_id"),
        )


class BaseAgent(ABC):
    """Abstract base for all swarm agents."""

    agent_type: AgentType

    def __init__(self, agent_id: str, state: SwarmState, tasks: list[TaskRecord]) -> None:
        self.agent_id = agent_id
        self._state = state
        self._tasks = tasks
        self._inbox: list[Message] = []
        self._outbox: list[Message] = []
        self._running = False

    @property
    def state(self) -> SwarmState:
        return self._state

    @property
    def tasks(self) -> list[TaskRecord]:
        return self._tasks

    def send_message(self, msg: Message) -> None:
        self._outbox.append(msg)

    def receive_message(self, msg: Message) -> None:
        self._inbox.append(msg)

    def process_messages(self) -> None:
        for msg in self._inbox:
            self._handle_message(msg)
        self._inbox.clear()

    @abstractmethod
    def _handle_message(self, msg: Message) -> None: ...

    @abstractmethod
    async def run(self) -> None: ...

    def register_in_state(self) -> None:
        record = AgentRecord(
            agent_id=self.agent_id,
            agent_type=self.agent_type.value,
            status="active",
            spawned_at=datetime.now(timezone.utc).isoformat(),
        )
        self._state.active_agents.append(record)
        save_state(self._state)

    def deregister_from_state(self) -> None:
        self._state.active_agents = [
            a for a in self._state.active_agents if a.agent_id != self.agent_id
        ]
        save_state(self._state)