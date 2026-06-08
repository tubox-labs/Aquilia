"""Recovery system — checkpoint-based rollback for swarm failures.

Provides:
- Checkpoint creation before every modification
- Automatic rollback on failure
- State persistence for crash recovery
- Resume capability after interruption
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .state import (
    SwarmState,
    TaskRecord,
    create_checkpoint,
    load_state,
    load_tasks,
    restore_checkpoint,
    save_state,
    save_tasks,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class RecoverySystem:
    """Handles checkpointing, rollback, and resume."""

    def __init__(self, state: SwarmState, tasks: list[TaskRecord]) -> None:
        self._state = state
        self._tasks = tasks
        self._checkpoints: dict[str, str] = {}

    def create_checkpoint(self) -> str:
        """Store the current HEAD as a recovery checkpoint."""
        checkpoint = create_checkpoint()
        self._state.last_checkpoint = checkpoint
        self._checkpoints[checkpoint] = checkpoint
        save_state(self._state)
        return checkpoint

    def rollback(self, checkpoint: str | None = None) -> bool:
        """Restore repository to a checkpoint."""
        target = checkpoint or self._state.last_checkpoint
        if not target:
            return False

        success = restore_checkpoint(target)
        if success:
            for task in self._tasks:
                if task.status == "in_progress":
                    task.status = "pending"
                    task.error = f"Rolled back to {target[:8]}"
            save_tasks(self._tasks)
        return success

    def mark_task_failed(self, task_id: str, error: str) -> None:
        """Mark a task as failed and increment retry count."""
        for task in self._tasks:
            if task.task_id == task_id:
                task.status = "failed"
                task.error = error
                task.retry_count += 1
                break
        save_tasks(self._tasks)

    def retry_failed_tasks(self) -> list[TaskRecord]:
        """Reset failed tasks to pending for retry."""
        retry_tasks: list[TaskRecord] = []
        for task in self._tasks:
            if task.status == "failed" and task.retry_count < 3:
                task.status = "pending"
                task.error = None
                retry_tasks.append(task)
        save_tasks(self._tasks)
        return retry_tasks

    def resume_state(self) -> tuple[SwarmState, list[TaskRecord]]:
        """Load state and tasks for crash recovery."""
        state = load_state()
        tasks = load_tasks()
        return state, tasks

    def get_progress(self) -> dict[str, Any]:
        """Return current progress statistics."""
        total = len(self._tasks)
        completed = sum(1 for t in self._tasks if t.status == "completed")
        failed = sum(1 for t in self._tasks if t.status == "failed")
        pending = sum(1 for t in self._tasks if t.status == "pending")
        in_progress = sum(1 for t in self._tasks if t.status == "in_progress")

        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "in_progress": in_progress,
            "percentage": round(completed / total * 100, 1) if total > 0 else 0,
            "last_checkpoint": self._state.last_checkpoint,
        }
