"""State management for the autonomous swarm system.

Provides atomic state persistence, checkpoint creation/restoration,
and task progress tracking across swarm sessions.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SWARM_DIR = Path(__file__).resolve().parent
STATE_PATH = SWARM_DIR / "state.json"
TASKS_PATH = SWARM_DIR / "tasks.json"
HISTORY_DIR = SWARM_DIR / "history"


@dataclass
class TaskRecord:
    """A single task in the execution plan."""

    task_id: str
    description: str
    dependencies: list[str] = field(default_factory=list)
    status: str = "pending"
    assigned_agent: str | None = None
    commit_hash: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    retry_count: int = 0
    error: str | None = None


@dataclass
class AgentRecord:
    """An active agent in the swarm."""

    agent_id: str
    agent_type: str
    status: str = "idle"
    current_task: str | None = None
    spawned_at: str | None = None


@dataclass
class SwarmState:
    """Complete swarm session state."""

    session_id: str | None = None
    status: str = "idle"
    started_at: str | None = None
    last_checkpoint: str | None = None
    completed_tasks: list[str] = field(default_factory=list)
    failed_tasks: list[str] = field(default_factory=list)
    active_agents: list[AgentRecord] = field(default_factory=list)
    current_task: str | None = None
    commit_count: int = 0
    tasks: list[TaskRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "status": self.status,
            "started_at": self.started_at,
            "last_checkpoint": self.last_checkpoint,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "active_agents": [
                {
                    "agent_id": a.agent_id,
                    "agent_type": a.agent_type,
                    "status": a.status,
                    "current_task": a.current_task,
                    "spawned_at": a.spawned_at,
                }
                for a in self.active_agents
            ],
            "current_task": self.current_task,
            "commit_count": self.commit_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SwarmState:
        return cls(
            session_id=data.get("session_id"),
            status=data.get("status", "idle"),
            started_at=data.get("started_at"),
            last_checkpoint=data.get("last_checkpoint"),
            completed_tasks=data.get("completed_tasks", []),
            failed_tasks=data.get("failed_tasks", []),
            active_agents=[
                AgentRecord(
                    agent_id=a["agent_id"],
                    agent_type=a["agent_type"],
                    status=a.get("status", "idle"),
                    current_task=a.get("current_task"),
                    spawned_at=a.get("spawned_at"),
                )
                for a in data.get("active_agents", [])
            ],
            current_task=data.get("current_task"),
            commit_count=data.get("commit_count", 0),
        )


def load_state() -> SwarmState:
    """Load swarm state from disk."""
    if STATE_PATH.exists():
        raw = json.loads(STATE_PATH.read_text())
        return SwarmState.from_dict(raw)

    st = SwarmState()
    save_state(st)
    return st


def save_state(state: SwarmState) -> None:
    """Persist swarm state atomically."""
    tmp = STATE_PATH.with_suffix(".tmp")
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(state.to_dict(), indent=2))
    os.replace(tmp, STATE_PATH)


def load_tasks() -> list[TaskRecord]:
    """Load task list from disk."""
    if TASKS_PATH.exists():
        raw = json.loads(TASKS_PATH.read_text())
        return [
            TaskRecord(
                task_id=t["task_id"],
                description=t["description"],
                dependencies=t.get("dependencies", []),
                status=t.get("status", "pending"),
                assigned_agent=t.get("assigned_agent"),
                commit_hash=t.get("commit_hash"),
                started_at=t.get("started_at"),
                completed_at=t.get("completed_at"),
                retry_count=t.get("retry_count", 0),
                error=t.get("error"),
            )
            for t in raw.get("tasks", [])
        ]
    return []


def save_tasks(tasks: list[TaskRecord]) -> None:
    """Persist task list atomically."""
    tmp = TASKS_PATH.with_suffix(".tmp")
    TASKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "tasks": [
            {
                "task_id": t.task_id,
                "description": t.description,
                "dependencies": t.dependencies,
                "status": t.status,
                "assigned_agent": t.assigned_agent,
                "commit_hash": t.commit_hash,
                "started_at": t.started_at,
                "completed_at": t.completed_at,
                "retry_count": t.retry_count,
                "error": t.error,
            }
            for t in tasks
        ],
        "total_count": len(tasks),
        "completed_count": sum(1 for t in tasks if t.status == "completed"),
        "failed_count": sum(1 for t in tasks if t.status == "failed"),
    }
    tmp.write_text(json.dumps(payload, indent=2))
    os.replace(tmp, TASKS_PATH)


def create_checkpoint() -> str:
    """Store a git checkpoint and return the commit hash."""
    import subprocess

    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        cwd=SWARM_DIR.parent,
    )
    return result.stdout.strip()


def restore_checkpoint(commit_hash: str) -> bool:
    """Restore repository to a previous checkpoint."""
    import subprocess

    result = subprocess.run(
        ["git", "reset", "--hard", commit_hash],
        capture_output=True,
        text=True,
        cwd=SWARM_DIR.parent,
    )
    return result.returncode == 0


def record_commit_in_history(
    commit_hash: str,
    agent_id: str,
    files: list[str],
    summary: str,
) -> None:
    """Append a commit record to the history directory."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    record = {
        "commit_hash": commit_hash,
        "timestamp": timestamp,
        "agent_id": agent_id,
        "files": files,
        "summary": summary,
    }
    entry_path = HISTORY_DIR / f"{commit_hash[:8]}.json"
    entry_path.write_text(json.dumps(record, indent=2))


def initialize_session() -> tuple[SwarmState, list[TaskRecord]]:
    """Start a new swarm session, loading or creating state."""
    state = load_state()
    tasks = load_tasks()
    state.session_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    state.started_at = datetime.now(timezone.utc).isoformat()
    state.status = "active"
    save_state(state)
    return state, tasks