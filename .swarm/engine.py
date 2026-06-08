"""Execution engine — the main entry point for swarm operations.

Provides CLI interface and programmatic API for:
- Starting a swarm session
- Executing task plans
- Monitoring progress
- Resuming after crashes
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

from .agents.coordinator import CoordinatorAgent
from .recovery import RecoverySystem
from .state import (
    SwarmState,
    TaskRecord,
    initialize_session,
)

ENGINE_ROOT = Path(__file__).resolve().parent


class ExecutionEngine:
    """Main entry point for the swarm system."""

    def __init__(self) -> None:
        self._state, self._tasks = initialize_session()
        self._coordinator: CoordinatorAgent | None = None
        self._recovery = RecoverySystem(self._state, self._tasks)

    @property
    def state(self) -> SwarmState:
        return self._state

    @property
    def tasks(self) -> list[TaskRecord]:
        return self._tasks

    def get_status(self) -> dict[str, Any]:
        """Return current swarm execution status."""
        stats = self._recovery.get_progress()
        stats["session_id"] = self._state.session_id
        stats["status"] = self._state.status
        stats["commit_count"] = self._state.commit_count
        stats["active_agents"] = len(self._state.active_agents)
        return stats

    async def execute(self, request: str) -> bool:
        """Execute a request using the full swarm pipeline."""
        self._coordinator = CoordinatorAgent(
            "coordinator_001", self._state, self._tasks
        )

        checkpoint = self._recovery.create_checkpoint()
        success = await self._coordinator.execute_plan(request)

        if not success:
            self._recovery.rollback(checkpoint)

        return success

    def resume(self) -> dict[str, Any]:
        """Resume a previously interrupted session."""
        self._state, self._tasks = self._recovery.resume_state()
        self._recovery = RecoverySystem(self._state, self._tasks)

        retry_tasks = self._recovery.retry_failed_tasks()
        return {
            "status": self._state.status,
            "tasks_resumed": len(retry_tasks),
            "total_pending": sum(1 for t in self._tasks if t.status == "pending"),
        }

    def print_status(self) -> None:
        """Pretty-print the current swarm status."""
        stats = self.get_status()
        print(f"Session: {stats['session_id']}")
        print(f"Status:  {stats['status']}")
        print(f"Tasks:   {stats['completed']}/{stats['total']} ({stats['percentage']}%)")
        print(f"Failed:  {stats['failed']}")
        print(f"Commits: {stats['commit_count']}")
        print(f"Agents:  {stats['active_agents']}")

    def list_tasks(self) -> None:
        """Print the task list with status indicators."""
        for task in self._tasks:
            icon = {
                "pending": "[ ]",
                "in_progress": "[>]",
                "completed": "[x]",
                "failed": "[!]",
            }.get(task.status, "[?]")
            deps = f" <- {', '.join(task.dependencies)}" if task.dependencies else ""
            print(f"{icon} {task.task_id}: {task.description}{deps}")


def cli_main() -> None:
    """CLI entry point for swarm operations."""
    if len(sys.argv) < 2:
        print("Usage: python -m .swarm.engine <command> [args]")
        print("Commands: status, execute <request>, resume, tasks")
        sys.exit(1)

    command = sys.argv[1]
    engine = ExecutionEngine()

    if command == "status":
        engine.print_status()
    elif command == "tasks":
        engine.list_tasks()
    elif command == "execute":
        request = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        if not request:
            print("Error: need a request to execute")
            sys.exit(1)
        success = asyncio.run(engine.execute(request))
        print(f"Execution {'successful' if success else 'partially completed'}")
    elif command == "resume":
        result = engine.resume()
        print(f"Resumed. {result['tasks_resumed']} tasks requeued.")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    cli_main()
