"""Planner Agent — analyzes user requests and generates execution plans.

Breaks work into atomic, dependency-ordered tasks and produces a task graph.
"""

from __future__ import annotations

import json
import uuid

from ..state import TaskRecord, save_tasks
from .base import AgentType, BaseAgent, Message, MessageType


class PlannerAgent(BaseAgent):
    """Generates task plans from user requests."""

    agent_type = AgentType.PLANNER

    def _handle_message(self, msg: Message) -> None:
        if msg.msg_type == MessageType.TASK_ASSIGNMENT:
            request = msg.payload.get("request", "")
            plan = self._create_plan(request)
            self._tasks = plan
            save_tasks(plan)
            response = Message(
                msg_id=str(uuid.uuid4()),
                msg_type=MessageType.TASK_COMPLETE,
                sender_id=self.agent_id,
                recipient_id=msg.sender_id,
                payload={"tasks": [t.task_id for t in plan], "plan": self._serialize_plan(plan)},
                correlation_id=msg.msg_id,
            )
            self.send_message(response)

    def _create_plan(self, request: str) -> list[TaskRecord]:
        """Analyze request and produce atomic tasks with dependencies."""
        tasks: list[TaskRecord] = []

        if "create" in request.lower() or "build" in request.lower() or "add" in request.lower():
            tasks.extend(self._parse_creation_tasks(request))
        elif "fix" in request.lower() or "refactor" in request.lower():
            tasks.extend(self._parse_modification_tasks(request))
        else:
            tasks.append(
                TaskRecord(
                    task_id=f"task_{len(tasks) + 1:03d}",
                    description=request,
                )
            )

        return tasks

    def _parse_creation_tasks(self, request: str) -> list[TaskRecord]:
        """Decompose a creation request into ordered atomic tasks."""
        tasks: list[TaskRecord] = []

        structure_task = TaskRecord(
            task_id="task_001",
            description=f"Set up directory structure for: {request}",
        )
        tasks.append(structure_task)

        impl_task = TaskRecord(
            task_id="task_002",
            description=f"Implement core logic for: {request}",
            dependencies=["task_001"],
        )
        tasks.append(impl_task)

        test_task = TaskRecord(
            task_id="task_003",
            description=f"Add tests for: {request}",
            dependencies=["task_002"],
        )
        tasks.append(test_task)

        doc_task = TaskRecord(
            task_id="task_004",
            description=f"Update documentation for: {request}",
            dependencies=["task_003"],
        )
        tasks.append(doc_task)

        return tasks

    def _parse_modification_tasks(self, request: str) -> list[TaskRecord]:
        """Decompose a modification request into ordered atomic tasks."""
        tasks: list[TaskRecord] = []

        analyze_task = TaskRecord(
            task_id="task_001",
            description=f"Analyze affected code for: {request}",
        )
        tasks.append(analyze_task)

        modify_task = TaskRecord(
            task_id="task_002",
            description=f"Apply modification for: {request}",
            dependencies=["task_001"],
        )
        tasks.append(modify_task)

        verify_task = TaskRecord(
            task_id="task_003",
            description=f"Verify modification: {request}",
            dependencies=["task_002"],
        )
        tasks.append(verify_task)

        return tasks

    def _serialize_plan(self, tasks: list[TaskRecord]) -> str:
        return json.dumps(
            {
                "tasks": [
                    {
                        "id": t.task_id,
                        "description": t.description,
                        "dependencies": t.dependencies,
                    }
                    for t in tasks
                ]
            },
            indent=2,
        )

    async def run(self) -> None:
        self.register_in_state()
        self.process_messages()
