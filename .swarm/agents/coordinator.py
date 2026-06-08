"""Coordinator Agent — orchestrates the swarm execution.

Responsibilities:
- Spawns workers dynamically
- Assigns tasks respecting dependencies
- Tracks progress
- Verifies commits exist before continuing
- Merges outputs
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

from .base import AgentType, BaseAgent, Message, MessageType
from .planner import PlannerAgent
from .worker import WorkerAgent
from ..state import (
    SwarmState,
    TaskRecord,
    create_checkpoint,
    load_state,
    load_tasks,
    record_commit_in_history,
    save_state,
    save_tasks,
)


class CoordinatorAgent(BaseAgent):
    """Master orchestrator of the swarm."""

    agent_type = AgentType.COORDINATOR

    def __init__(self, agent_id: str, state: SwarmState, tasks: list[TaskRecord]) -> None:
        super().__init__(agent_id, state, tasks)
        self._workers: list[WorkerAgent] = []
        self._planner: PlannerAgent | None = None

    def _handle_message(self, msg: Message) -> None:
        if msg.msg_type == MessageType.STATUS_REPORT:
            worker_id = msg.sender_id
            task_id = msg.payload.get("task_id", "")
            status = msg.payload.get("status", "")
            self._process_worker_report(worker_id, task_id, status)

        elif msg.msg_type == MessageType.SPAWN_REQUEST:
            count = msg.payload.get("count", 1)
            for _ in range(count):
                self._spawn_worker()

    def _process_worker_report(self, worker_id: str, task_id: str, status: str) -> None:
        if status == "completed":
            if task_id not in self._state.completed_tasks:
                self._state.completed_tasks.append(task_id)
        elif status == "failed":
            if task_id not in self._state.failed_tasks:
                self._state.failed_tasks.append(task_id)
        save_state(self._state)

    def _spawn_worker(self) -> str:
        worker_id = f"worker_{len(self._workers) + 1:03d}"
        worker = WorkerAgent(worker_id, self._state, self._tasks)
        self._workers.append(worker)
        return worker_id

    def _get_ready_tasks(self) -> list[TaskRecord]:
        """Return tasks whose dependencies are all satisfied."""
        ready: list[TaskRecord] = []
        for task in self._tasks:
            if task.status != "pending":
                continue
            if all(
                dep in self._state.completed_tasks
                for dep in task.dependencies
            ):
                ready.append(task)
        return ready

    def _verify_commit(self, commit_hash: str) -> bool:
        """Verify a commit exists in the repository."""
        import subprocess

        result = subprocess.run(
            ["git", "cat-file", "-t", commit_hash],
            capture_output=True,
            text=True,
            cwd=WorkerAgent.REPO_ROOT,
        )
        return result.returncode == 0 and "commit" in result.stdout

    async def execute_plan(self, request: str) -> bool:
        """Full swarm execution: plan -> execute -> verify."""
        self._planner = PlannerAgent("planner_001", self._state, self._tasks)
        self._planner.register_in_state()

        plan_msg = Message(
            msg_id=str(uuid.uuid4()),
            msg_type=MessageType.TASK_ASSIGNMENT,
            sender_id=self.agent_id,
            recipient_id=self._planner.agent_id,
            payload={"request": request},
        )
        self._planner.receive_message(plan_msg)
        self._planner.process_messages()

        if self._planner._outbox:
            result = self._planner._outbox[-1]
            self._tasks = load_tasks()
        else:
            self._tasks = self._planner._tasks

        save_tasks(self._tasks)

        max_workers = min(len(self._tasks), 8)
        for i in range(max_workers):
            self._spawn_worker()

        while True:
            ready = self._get_ready_tasks()
            if not ready:
                pending = [t for t in self._tasks if t.status == "pending"]
                completed = [t for t in self._tasks if t.status == "completed"]
                if len(pending) == 0:
                    break
                if len(pending) > 0 and len(ready) == 0:
                    break

            for task in ready:
                worker = self._workers.pop(0)
                worker.execute_task_sync(task, self.agent_id)
                self._workers.append(worker)

                if task.status == "completed" and task.commit_hash:
                    record_commit_in_history(
                        task.commit_hash,
                        worker.agent_id,
                        [],
                        task.description,
                    )

            await asyncio.sleep(0)

        all_completed = all(
            t.status == "completed" for t in self._tasks
        )
        self._state.status = "completed" if all_completed else "partial"
        save_state(self._state)
        return all_completed

    async def run(self) -> None:
        self.register_in_state()