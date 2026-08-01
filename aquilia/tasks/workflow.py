"""
AquilaTasks — Workflows: chains, groups, chords, and DAGs.

Composes registered ``@task`` functions into multi-step pipelines that the
existing worker pool executes.  Nothing here runs jobs itself: a workflow is
*compiled* into ordinary :class:`~aquilia.tasks.job.Job` objects wired
together by ``depends_on``, and the backend's dependency gating does the rest.

That is the whole design decision.  A separate workflow executor would need
its own scheduling, retry, and persistence, and would drift from the task
engine's.  By expressing dependencies on the job itself, workflows inherit
retries, backoff, dead-lettering, leases, and every backend — including the
distributed ones — for free.

Primitives:
    :func:`chain`
        Sequential. Each step waits for the previous one.
    :func:`group`
        Parallel. All steps run concurrently, limited only by worker count.
    :func:`chord`
        Fan-out then fan-in: a group, then a callback receiving the group's
        results.
    :class:`Workflow`
        Arbitrary DAG, when the shapes above are not enough.

Examples::

    from aquilia.tasks import chain, group, chord

    # Sequential pipeline
    await chain(
        fetch_data.s(source="api"),
        transform.s(),
        publish.s(),
    ).run(manager)

    # Parallel fan-out
    await group(
        resize.s(image_id=1),
        resize.s(image_id=2),
    ).run(manager)

    # Fan-out then aggregate
    await chord(
        group(shard_report.s(n) for n in range(4)),
        merge_reports.s(),
    ).run(manager)

    # Explicit DAG
    wf = Workflow("nightly")
    extract = wf.add(extract_rows.s())
    clean = wf.add(clean_rows.s(), depends_on=[extract])
    audit = wf.add(audit_rows.s(), depends_on=[extract])
    wf.add(publish.s(), depends_on=[clean, audit])
    await wf.run(manager)

Result passing:
    A step declared with :meth:`Signature.with_parent_results` receives its
    dependencies' return values as a ``parent_results`` keyword.  Chord
    callbacks receive them automatically.  Results are read from the backend
    at execution time, so they survive a restart when the backend is
    persistent.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Sequence
from typing import Any

from aquilia.tasks.faults import TaskWorkflowFault
from aquilia.tasks.job import Priority

__all__ = [
    "Signature",
    "Workflow",
    "WorkflowResult",
    "chain",
    "chord",
    "group",
]


class Signature:
    """
    A task plus the arguments it will be called with, not yet enqueued.

    Equivalent to Celery's signature: it captures *what to run* so a workflow
    can wire dependencies before anything is dispatched.

    Build one with :meth:`~aquilia.tasks.decorators._TaskDescriptor.s` rather
    than constructing directly::

        send_email.s(to="a@b.co", subject="Hi")

    Args:
        task: A ``@task`` descriptor or plain async callable.
        args: Positional arguments.
        kwargs: Keyword arguments.
        queue: Queue override for this step.
        priority: Priority override for this step.
        pass_parent_results: When True, the step receives a ``parent_results``
            keyword holding its dependencies' return values, in declaration
            order.

    Examples::

        step = transform.s(mode="strict")
        step_with_input = publish.s().with_parent_results()
    """

    __slots__ = ("task", "args", "kwargs", "queue", "priority", "pass_parent_results")

    def __init__(
        self,
        task: Any,
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
        *,
        queue: str | None = None,
        priority: Priority | None = None,
        pass_parent_results: bool = False,
    ) -> None:
        self.task = task
        self.args = args
        self.kwargs = kwargs or {}
        self.queue = queue
        self.priority = priority
        self.pass_parent_results = pass_parent_results

    def with_parent_results(self) -> Signature:
        """
        Return a copy that receives dependency results as ``parent_results``.

        Examples::

            merge.s().with_parent_results()
            # merge(parent_results=[...]) at execution time
        """
        return Signature(
            self.task,
            self.args,
            dict(self.kwargs),
            queue=self.queue,
            priority=self.priority,
            pass_parent_results=True,
        )

    def __repr__(self) -> str:
        name = getattr(self.task, "task_name", getattr(self.task, "__name__", repr(self.task)))
        return f"Signature({name}, args={self.args!r}, kwargs={self.kwargs!r})"


class WorkflowResult:
    """
    Handle for a dispatched workflow.

    Attributes:
        workflow_id: Groups every job produced by this workflow.
        job_ids: Enqueued job IDs, in declaration order.
        terminal_ids: Jobs with no dependents — the workflow is finished when
            all of these are terminal.

    Examples::

        result = await wf.run(manager)
        if await result.is_complete(manager):
            values = await result.results(manager)
    """

    __slots__ = ("workflow_id", "job_ids", "terminal_ids")

    def __init__(self, workflow_id: str, job_ids: list[str], terminal_ids: list[str]) -> None:
        self.workflow_id = workflow_id
        self.job_ids = job_ids
        self.terminal_ids = terminal_ids

    async def is_complete(self, manager: Any) -> bool:
        """
        Whether every terminal job has finished.

        Returns:
            ``True`` when all leaf jobs reached a terminal state — including
            failure.  Use :meth:`failed_jobs` to distinguish success.
        """
        for job_id in self.terminal_ids:
            job = await manager.get_job(job_id)
            if job is None or not job.is_terminal:
                return False
        return True

    async def failed_jobs(self, manager: Any) -> list[Any]:
        """Return workflow jobs that ended in a failed or dead state."""
        from aquilia.tasks.job import JobState

        failed = []
        for job_id in self.job_ids:
            job = await manager.get_job(job_id)
            if job and job.state in (JobState.FAILED, JobState.DEAD):
                failed.append(job)
        return failed

    async def results(self, manager: Any) -> list[Any]:
        """Return the terminal jobs' return values, in declaration order."""
        values = []
        for job_id in self.terminal_ids:
            job = await manager.get_job(job_id)
            values.append(job.result.value if job and job.result else None)
        return values

    def __repr__(self) -> str:
        return f"WorkflowResult(workflow_id={self.workflow_id!r}, jobs={len(self.job_ids)})"


class _Node:
    """One step in a workflow graph: a signature plus its dependency indices."""

    __slots__ = ("signature", "depends_on", "job_id")

    def __init__(self, signature: Signature, depends_on: list[int]) -> None:
        self.signature = signature
        self.depends_on = depends_on
        self.job_id = uuid.uuid4().hex[:16]


class Workflow:
    """
    A directed acyclic graph of tasks.

    Use when the work is not a plain chain or group — a diamond, a partial
    fan-out, or any mix.  :func:`chain`, :func:`group`, and :func:`chord` are
    thin builders over this class.

    Validation:
        Cycles are rejected at :meth:`run` rather than at execution time.  A
        cyclic graph would deadlock silently — every node waiting on a
        dependency that can never complete, with no worker making progress and
        nothing to show in the dashboard.

    Args:
        name: Label recorded on each job, for dashboards and debugging.

    Examples::

        wf = Workflow("nightly-etl")
        extract = wf.add(extract_rows.s())
        clean = wf.add(clean_rows.s(), depends_on=[extract])
        audit = wf.add(audit_rows.s(), depends_on=[extract])
        wf.add(publish.s().with_parent_results(), depends_on=[clean, audit])

        result = await wf.run(manager)
    """

    def __init__(self, name: str = "workflow") -> None:
        self.name = name
        self.workflow_id = uuid.uuid4().hex[:16]
        self._nodes: list[_Node] = []

    def add(self, signature: Signature, *, depends_on: Sequence[int] | None = None) -> int:
        """
        Add a step to the graph.

        Args:
            signature: The task and arguments to run.
            depends_on: Indices of steps that must complete first, as returned
                by earlier :meth:`add` calls.

        Returns:
            This step's index, to be used as a dependency by later steps.

        Raises:
            TaskWorkflowFault: If a dependency index does not exist.  Forward
                references are rejected because they cannot be satisfied — a
                step can only depend on something already declared.
        """
        deps = list(depends_on or [])
        for dep in deps:
            if dep < 0 or dep >= len(self._nodes):
                raise TaskWorkflowFault(
                    f"step {len(self._nodes)} depends on unknown step {dep} "
                    f"(only steps 0..{len(self._nodes) - 1} are declared)"
                )
        self._nodes.append(_Node(signature, deps))
        return len(self._nodes) - 1

    def _validate(self) -> None:
        """Reject empty and cyclic graphs before anything is enqueued."""
        if not self._nodes:
            raise TaskWorkflowFault("workflow has no steps")

        # Indices only ever reference earlier nodes, so a cycle is impossible
        # by construction; verify anyway so a future edit cannot regress it.
        visiting: set[int] = set()
        done: set[int] = set()

        def visit(index: int, path: tuple[int, ...]) -> None:
            if index in done:
                return
            if index in visiting:
                cycle = " -> ".join(str(p) for p in (*path, index))
                raise TaskWorkflowFault(f"dependency cycle detected: {cycle}")
            visiting.add(index)
            for dep in self._nodes[index].depends_on:
                visit(dep, (*path, index))
            visiting.discard(index)
            done.add(index)

        for i in range(len(self._nodes)):
            visit(i, ())

    @property
    def terminal_indices(self) -> list[int]:
        """Indices of steps nothing else depends on — the workflow's outputs."""
        depended_upon = {dep for node in self._nodes for dep in node.depends_on}
        return [i for i in range(len(self._nodes)) if i not in depended_upon]

    async def run(self, manager: Any) -> WorkflowResult:
        """
        Compile the graph into jobs and enqueue them.

        Every job is created up front with its dependencies already recorded,
        so the graph is fully durable the moment this returns.  Dependent jobs
        start in ``WAITING`` and the backend releases them as their
        dependencies complete — no orchestrator process is required, and the
        workflow survives a restart on a persistent backend.

        Args:
            manager: The :class:`~aquilia.tasks.engine.TaskManager` to enqueue on.

        Returns:
            A :class:`WorkflowResult` for polling progress.

        Raises:
            TaskWorkflowFault: If the graph is empty or cyclic.
            TaskSerializationFault: If a step's arguments are not JSON-safe and
                the backend is persistent.

        Examples::

            result = await wf.run(manager)
            while not await result.is_complete(manager):
                await asyncio.sleep(0.5)
        """
        self._validate()

        from aquilia.tasks.job import JobState

        job_ids: list[str] = []
        for node in self._nodes:
            sig = node.signature
            dep_ids = [self._nodes[i].job_id for i in node.depends_on]

            kwargs = dict(sig.kwargs)
            if sig.pass_parent_results:
                # Marker consumed by TaskManager._execute_job, which swaps it
                # for the real results at execution time. Storing the marker
                # rather than the values keeps the job JSON-serialisable and
                # lets results be read after a restart.
                kwargs["parent_results"] = _PARENT_RESULTS_MARKER

            await manager.enqueue(
                sig.task,
                *sig.args,
                queue=sig.queue,
                priority=sig.priority,
                job_id=node.job_id,
                depends_on=dep_ids,
                workflow_id=self.workflow_id,
                initial_state=JobState.WAITING if dep_ids else None,
                metadata={"workflow": self.name},
                **kwargs,
            )
            job_ids.append(node.job_id)

        return WorkflowResult(
            workflow_id=self.workflow_id,
            job_ids=job_ids,
            terminal_ids=[self._nodes[i].job_id for i in self.terminal_indices],
        )

    def __repr__(self) -> str:
        return f"Workflow(name={self.name!r}, steps={len(self._nodes)})"


#: Sentinel stored in a job's kwargs, replaced with real dependency results
#: at execution time.  A string is used so the job stays JSON-serialisable.
_PARENT_RESULTS_MARKER = "__aquilia_parent_results__"


def chain(*signatures: Signature, name: str = "chain") -> Workflow:
    """
    Run steps strictly in sequence.

    Each step waits for the previous one to complete successfully.  If a step
    exhausts its retries, everything after it stays ``WAITING`` rather than
    running on missing input.

    Args:
        *signatures: Steps, in execution order.
        name: Workflow label.

    Returns:
        A :class:`Workflow` ready to :meth:`~Workflow.run`.

    Raises:
        TaskWorkflowFault: If no steps are given.

    Examples::

        await chain(
            fetch.s(url="..."),
            parse.s().with_parent_results(),
            store.s(),
        ).run(manager)
    """
    if not signatures:
        raise TaskWorkflowFault("chain() requires at least one task")

    wf = Workflow(name)
    previous: int | None = None
    for sig in signatures:
        previous = wf.add(sig, depends_on=[previous] if previous is not None else None)
    return wf


def group(signatures: Iterable[Signature], *, name: str = "group") -> Workflow:
    """
    Run steps concurrently.

    Every step is independent, so throughput is bounded only by worker count
    and — on a distributed backend — by how many machines are running workers.

    Args:
        signatures: Steps to run in parallel.
        name: Workflow label.

    Returns:
        A :class:`Workflow` ready to :meth:`~Workflow.run`.

    Raises:
        TaskWorkflowFault: If the iterable is empty.

    Examples::

        await group(resize.s(image_id=i) for i in image_ids).run(manager)
    """
    sigs = list(signatures)
    if not sigs:
        raise TaskWorkflowFault("group() requires at least one task")

    wf = Workflow(name)
    for sig in sigs:
        wf.add(sig)
    return wf


def chord(header: Workflow | Iterable[Signature], callback: Signature, *, name: str = "chord") -> Workflow:
    """
    Fan out, then aggregate.

    Runs a group of tasks in parallel, then a single callback once *all* of
    them complete.  The callback receives their return values as
    ``parent_results``.

    Args:
        header: The parallel steps — a :class:`Workflow` built by
            :func:`group`, or a plain iterable of signatures.
        callback: The aggregation step.  Result passing is enabled
            automatically; calling ``.with_parent_results()`` yourself is
            harmless.
        name: Workflow label.

    Returns:
        A :class:`Workflow` ready to :meth:`~Workflow.run`.

    Raises:
        TaskWorkflowFault: If the header is empty.

    Examples::

        await chord(
            group(count_shard.s(shard=i) for i in range(8)),
            sum_counts.s(),
        ).run(manager)

        # sum_counts(parent_results=[c0, c1, ..., c7])
    """
    header_sigs = [node.signature for node in header._nodes] if isinstance(header, Workflow) else list(header)
    if not header_sigs:
        raise TaskWorkflowFault("chord() requires at least one header task")

    wf = Workflow(name)
    indices = [wf.add(sig) for sig in header_sigs]
    wf.add(callback.with_parent_results(), depends_on=indices)
    return wf
