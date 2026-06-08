"""Worker Agent — executes individual tasks with the sequential commit protocol.

Workers are the primary workhorse agents. Each worker:
1. Receives a task
2. Implements the change
3. Requests review
4. Requests tests
5. Requests commit
6. Terminates

Workers NEVER directly continue to another task — the coordinator assigns
the next task after verifying the commit exists.
"""

from __future__ import annotations

import subprocess
import uuid
from pathlib import Path

from ..state import TaskRecord, save_state, save_tasks
from .base import AgentType, BaseAgent, Message, MessageType


class WorkerAgent(BaseAgent):
    """Task execution worker following sequential commit protocol."""

    agent_type = AgentType.WORKER
    REPO_ROOT: Path = Path(__file__).resolve().parent.parent.parent

    def _handle_message(self, msg: Message) -> None:
        pass

    def execute_task_sync(self, task: TaskRecord, coordinator_id: str) -> bool:
        """Execute a task synchronously, following the full protocol pipeline."""
        self._state.current_task = task.task_id
        task.status = "in_progress"
        task.assigned_agent = self.agent_id
        save_tasks(self._tasks)
        save_state(self._state)

        checkpoint = self._git_rev_parse_head()

        try:
            self._implement_change(task)
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            save_tasks(self._tasks)
            if checkpoint:
                subprocess.run(
                    ["git", "reset", "--hard", checkpoint],
                    capture_output=True,
                    text=True,
                    cwd=self.REPO_ROOT,
                )
            return False

        files = self._get_changed_files()

        review_passed = self._request_review_sync(files, task.task_id, coordinator_id)
        if not review_passed:
            task.status = "failed"
            task.error = "Review rejected"
            save_tasks(self._tasks)
            if checkpoint:
                subprocess.run(
                    ["git", "reset", "--hard", checkpoint],
                    capture_output=True,
                    text=True,
                    cwd=self.REPO_ROOT,
                )
            return False

        tests_passed = self._request_tests_sync(task.task_id, coordinator_id)
        if not tests_passed:
            task.status = "failed"
            task.error = "Tests failed"
            save_tasks(self._tasks)
            if checkpoint:
                subprocess.run(
                    ["git", "reset", "--hard", checkpoint],
                    capture_output=True,
                    text=True,
                    cwd=self.REPO_ROOT,
                )
            return False

        success, commit_hash = self._request_commit_sync(
            task, files, coordinator_id
        )
        if not success:
            task.status = "failed"
            task.error = "Commit failed"
            save_tasks(self._tasks)
            if checkpoint:
                subprocess.run(
                    ["git", "reset", "--hard", checkpoint],
                    capture_output=True,
                    text=True,
                    cwd=self.REPO_ROOT,
                )
            return False

        self._request_changelog_sync(commit_hash, files, task, coordinator_id)

        task.status = "completed"
        task.commit_hash = commit_hash
        self._state.completed_tasks.append(task.task_id)
        self._state.commit_count += 1
        save_tasks(self._tasks)
        save_state(self._state)

        return True

    def _implement_change(self, task: TaskRecord) -> None:
        """Apply the code change for this task. Subclasses override this."""
        pass

    def _git_rev_parse_head(self) -> str:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=self.REPO_ROOT,
        )
        return result.stdout.strip()

    def _get_changed_files(self) -> list[str]:
        result = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            capture_output=True,
            text=True,
            cwd=self.REPO_ROOT,
        )
        staged = result.stdout.strip().split("\n") if result.stdout.strip() else []

        result2 = subprocess.run(
            ["git", "diff", "--name-only"],
            capture_output=True,
            text=True,
            cwd=self.REPO_ROOT,
        )
        unstaged = result2.stdout.strip().split("\n") if result2.stdout.strip() else []

        return sorted(set(staged + unstaged))

    def _request_review_sync(
        self, files: list[str], task_id: str, coordinator_id: str
    ) -> bool:
        from .base import Message
        from .review import ReviewAgent

        review_agent = ReviewAgent("review_sync", self._state, self._tasks)
        review_agent.register_in_state()

        request = Message(
            msg_id=str(uuid.uuid4()),
            msg_type=MessageType.REVIEW_REQUEST,
            sender_id=self.agent_id,
            recipient_id=review_agent.agent_id,
            payload={"files": files, "task_id": task_id},
        )
        review_agent.receive_message(request)
        review_agent.process_messages()

        if review_agent._outbox:
            result = review_agent._outbox[0]
            return result.payload.get("approved", False)
        return False

    def _request_tests_sync(self, task_id: str, coordinator_id: str) -> bool:
        from .test import TestAgent

        test_agent = TestAgent("test_sync", self._state, self._tasks)
        test_agent.register_in_state()

        request = Message(
            msg_id=str(uuid.uuid4()),
            msg_type=MessageType.TEST_REQUEST,
            sender_id=self.agent_id,
            recipient_id=test_agent.agent_id,
            payload={"scope": "style", "task_id": task_id},
        )
        test_agent.receive_message(request)
        test_agent.process_messages()

        if test_agent._outbox:
            result = test_agent._outbox[0]
            return result.payload.get("passed", False)
        return False

    def _request_commit_sync(
        self, task: TaskRecord, files: list[str], coordinator_id: str
    ) -> tuple[bool, str]:
        from .commit import CommitAgent

        commit_agent = CommitAgent("commit_sync", self._state, self._tasks)
        commit_agent.register_in_state()

        request = Message(
            msg_id=str(uuid.uuid4()),
            msg_type=MessageType.COMMIT_REQUEST,
            sender_id=self.agent_id,
            recipient_id=commit_agent.agent_id,
            payload={
                "type": "feat",
                "summary": task.description,
                "files": files,
                "reason": f"Worker {self.agent_id} executed task {task.task_id}",
                "task_id": task.task_id,
            },
        )
        commit_agent.receive_message(request)
        commit_agent.process_messages()

        if commit_agent._outbox:
            result = commit_agent._outbox[0]
            return result.payload.get("success", False), result.payload.get("commit_hash", "")
        return False, ""

    def _request_changelog_sync(
        self, commit_hash: str, files: list[str], task: TaskRecord, coordinator_id: str
    ) -> None:
        from .changelog import ChangeLogAgent

        log_agent = ChangeLogAgent("changelog_sync", self._state, self._tasks)
        log_agent.register_in_state()

        request = Message(
            msg_id=str(uuid.uuid4()),
            msg_type=MessageType.CHANGELOG_UPDATE,
            sender_id=self.agent_id,
            recipient_id=log_agent.agent_id,
            payload={
                "commit_hash": commit_hash,
                "agent_id": self.agent_id,
                "files": files,
                "summary": task.description,
            },
        )
        log_agent.receive_message(request)
        log_agent.process_messages()

    async def run(self) -> None:
        self.register_in_state()
        self.process_messages()
