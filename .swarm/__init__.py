"""Autonomous Sequential Commit Swarm System.

A multi-agent swarm that executes code changes as a sequence of
small, well-documented, independently-reviewed commits.

Architecture
------------
    .swarm/
    ├── __init__.py          ← this file — public API
    ├── state.py             ← state management & persistence
    ├── recovery.py          ← checkpoint/rollback/resume
    ├── engine.py            ← execution engine & CLI
    ├── agents/
    │   ├── __init__.py
    │   ├── base.py          ← BaseAgent, Message, enums
    │   ├── planner.py       ← task decomposition
    │   ├── coordinator.py   ← swarm orchestration
    │   ├── worker.py        ← task execution
    │   ├── commit.py        ← git commit execution
    │   ├── changelog.py     ← CHANGES.md maintenance
    │   ├── review.py        ← code review gate
    │   └── test.py          ← test/lint gate
    ├── state.json           ← current session state
    ├── tasks.json           ← task plan & progress
    └── history/             ← per-commit records

Usage
-----
    from .swarm.engine import ExecutionEngine

    engine = ExecutionEngine()
    asyncio.run(engine.execute("add user authentication"))

CLI
---
    python -m .swarm.engine status
    python -m .swarm.engine execute "add rate limiting"
    python -m .swarm.engine resume
    python -m .swarm.engine tasks

Protocol
--------
    Task Received → Implement → Review → Tests → CHANGES.md → Commit → Next
"""

from __future__ import annotations

from .agents.base import (
    AgentType,
    BaseAgent,
    Message,
    MessageType,
)
from .agents.changelog import ChangeLogAgent
from .agents.commit import CommitAgent
from .agents.coordinator import CoordinatorAgent
from .agents.planner import PlannerAgent
from .agents.review import ReviewAgent
from .agents.test import TestAgent
from .agents.worker import WorkerAgent
from .engine import ExecutionEngine, cli_main
from .recovery import RecoverySystem
from .state import (
    AgentRecord,
    SwarmState,
    TaskRecord,
    create_checkpoint,
    initialize_session,
    load_state,
    load_tasks,
    record_commit_in_history,
    restore_checkpoint,
    save_state,
    save_tasks,
)

__version__ = "1.0.0"

__all__ = [
    "AgentRecord",
    "AgentType",
    "BaseAgent",
    "ChangeLogAgent",
    "CommitAgent",
    "CoordinatorAgent",
    "ExecutionEngine",
    "Message",
    "MessageType",
    "PlannerAgent",
    "RecoverySystem",
    "ReviewAgent",
    "SwarmState",
    "TaskRecord",
    "TestAgent",
    "WorkerAgent",
    "cli_main",
    "create_checkpoint",
    "initialize_session",
    "load_state",
    "load_tasks",
    "record_commit_in_history",
    "restore_checkpoint",
    "save_state",
    "save_tasks",
]
