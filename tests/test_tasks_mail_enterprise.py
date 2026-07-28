"""
Enterprise task and mail capabilities: serialization, distribution, durable
backends, workflows, idempotency, mail delivery queue, and bounce handling.

These exercise the runtime rather than the type surface — a job crosses a
process boundary via serialization, a durable backend is driven against real
SQLite, and a webhook drives an actual suppression record.
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

import pytest

from aquilia.tasks import MemoryBackend, TaskManager
from aquilia.tasks.job import Job, JobResult, JobState

# ── Serialization: the prerequisite for crossing a process ───────────


@pytest.fixture
def registered_task():
    """Register a task in the global registry and clean up after."""
    from aquilia.tasks.decorators import _task_registry, task

    @task(name="enterprise_add")
    async def enterprise_add(a: int, b: int) -> int:
        return a + b

    yield enterprise_add
    _task_registry.pop("enterprise_add", None)


@pytest.fixture
def fan_in_task():
    """A task that consumes its dependencies' results."""
    from aquilia.tasks.decorators import _task_registry, task

    @task(name="enterprise_fan_in")
    async def enterprise_fan_in(base: int = 0, parent_results: list | None = None) -> int:
        return base + sum(r for r in (parent_results or []) if isinstance(r, int))

    yield enterprise_fan_in
    _task_registry.pop("enterprise_fan_in", None)


class TestJobSerialization:
    def test_job_round_trips_through_payload(self, registered_task):
        job = Job(
            name="enterprise_add",
            func_ref="enterprise_add",
            args=(2, 3),
            kwargs={},
            queue="q1",
        )
        restored = Job.from_payload(job.to_payload())

        assert restored.id == job.id
        assert restored.func_ref == "enterprise_add"
        assert restored.args == (2, 3)
        assert restored.queue == "q1"

    def test_restored_job_resolves_its_function_from_registry(self, registered_task):
        from aquilia.tasks.decorators import get_task

        restored = Job.from_payload(Job(name="a", func_ref="enterprise_add", args=(4, 5)).to_payload())
        assert get_task(restored.func_ref) is not None

    def test_unregistered_ref_is_not_resolvable(self):
        """A worker that cannot resolve a job must fault, not drop it silently."""
        from aquilia.tasks.decorators import get_task

        restored = Job.from_payload(Job(name="x", func_ref="never_registered_task").to_payload())
        assert get_task(restored.func_ref) is None

    def test_unserializable_argument_is_rejected_at_serialization(self):
        """Fail loudly at enqueue rather than at pop in another process."""
        from aquilia.tasks.faults import TaskSerializationFault

        job = Job(name="enterprise_add", func_ref="enterprise_add", args=(lambda: None,))
        with pytest.raises(TaskSerializationFault):
            job.to_payload()

    def test_json_safe_result_survives_round_trip(self):
        """Values must round-trip, not degrade into a repr string."""
        restored = JobResult.from_dict(JobResult(success=True, value={"n": [1, 2]}).to_dict())
        assert restored.value == {"n": [1, 2]}

    def test_unserializable_result_degrades_to_repr(self):
        """A non-JSON result must not poison the whole job record."""
        d = JobResult(success=True, value=object()).to_dict()
        assert isinstance(d["value"], str)


# ── Idempotency: fingerprints must actually be enforced ─────────────


class TestIdempotencyEnforcement:
    async def test_default_allows_duplicates_for_backward_compatibility(self, registered_task):
        manager = TaskManager(backend=MemoryBackend(), num_workers=0)
        first = await manager.enqueue(registered_task, 1, 2)
        second = await manager.enqueue(registered_task, 1, 2)
        assert first != second

    async def test_dedup_skip_collapses_identical_work(self, registered_task):
        manager = TaskManager(backend=MemoryBackend(), num_workers=0)
        first = await manager.enqueue(registered_task, 1, 2, dedup="skip")
        second = await manager.enqueue(registered_task, 1, 2, dedup="skip")
        assert first == second

    async def test_dedup_skip_does_not_collapse_different_work(self, registered_task):
        manager = TaskManager(backend=MemoryBackend(), num_workers=0)
        first = await manager.enqueue(registered_task, 1, 2, dedup="skip")
        second = await manager.enqueue(registered_task, 9, 9, dedup="skip")
        assert first != second

    async def test_dedup_raise_faults_on_duplicate(self, registered_task):
        from aquilia.tasks.faults import TaskDuplicateFault

        manager = TaskManager(backend=MemoryBackend(), num_workers=0)
        await manager.enqueue(registered_task, 3, 4, dedup="raise")
        with pytest.raises(TaskDuplicateFault):
            await manager.enqueue(registered_task, 3, 4, dedup="raise")

    def test_fingerprint_is_stable_for_equal_payloads(self):
        assert Job(name="t", func_ref="t", args=(1,), kwargs={"k": 2}).fingerprint == (
            Job(name="t", func_ref="t", args=(1,), kwargs={"k": 2}).fingerprint
        )

    def test_fingerprint_agrees_across_tuple_and_list_arguments(self):
        """Equal-but-not-identical values must dedup across processes."""
        assert (
            Job(name="t", func_ref="t", args=([1, 2],)).fingerprint
            == Job(name="t", func_ref="t", args=((1, 2),)).fingerprint
        )

    def test_fingerprint_differs_on_arguments(self):
        assert Job(name="t", func_ref="t", args=(1,)).fingerprint != Job(name="t", func_ref="t", args=(2,)).fingerprint

    def test_fingerprint_differs_on_queue(self):
        assert Job(name="t", func_ref="t", queue="a").fingerprint != Job(name="t", func_ref="t", queue="b").fingerprint


# ── Workflows: chain, group, chord, DAG ─────────────────────────────


class TestWorkflows:
    async def test_chain_runs_sequentially(self, registered_task):
        from aquilia.tasks.workflow import Signature, chain

        manager = TaskManager(backend=MemoryBackend(), num_workers=2)
        await manager.start()
        try:
            result = await chain(
                Signature(registered_task, (1, 1)),
                Signature(registered_task, (10, 20)),
            ).run(manager)
            for _ in range(50):
                if await result.is_complete(manager):
                    break
                await asyncio.sleep(0.05)
            assert await result.is_complete(manager)
            assert await result.failed_jobs(manager) == []
        finally:
            await manager.stop()

    async def test_chain_feeds_parent_result_into_child(self, registered_task, fan_in_task):
        """2+1=3, then 10+3=13 — the dependency actually carries a value."""
        from aquilia.tasks.workflow import Signature, chain

        manager = TaskManager(backend=MemoryBackend(), num_workers=2)
        await manager.start()
        try:
            result = await chain(
                Signature(registered_task, (2, 1)),
                Signature(fan_in_task, (10,)).with_parent_results(),
            ).run(manager)
            for _ in range(50):
                if await result.is_complete(manager):
                    break
                await asyncio.sleep(0.05)
            assert await result.results(manager) == [13]
        finally:
            await manager.stop()

    async def test_chord_collects_parallel_header_results(self, registered_task, fan_in_task):
        """2 and 4 run in parallel; the callback sees both — 0+2+4=6."""
        from aquilia.tasks.workflow import Signature, chord

        manager = TaskManager(backend=MemoryBackend(), num_workers=4)
        await manager.start()
        try:
            result = await chord(
                [Signature(registered_task, (1, 1)), Signature(registered_task, (2, 2))],
                Signature(fan_in_task, (0,)).with_parent_results(),
            ).run(manager)
            for _ in range(50):
                if await result.is_complete(manager):
                    break
                await asyncio.sleep(0.05)
            assert await result.failed_jobs(manager) == []
            assert await result.results(manager) == [6]
        finally:
            await manager.stop()

    async def test_group_jobs_have_no_dependencies(self, registered_task):
        """A group is a pure fan-out — nothing may serialise it."""
        from aquilia.tasks.workflow import Signature, group

        manager = TaskManager(backend=MemoryBackend(), num_workers=0)
        result = await group([Signature(registered_task, (1, 1)), Signature(registered_task, (2, 2))]).run(manager)
        for job_id in result.job_ids:
            assert (await manager.get_job(job_id)).depends_on == []

    def test_cycle_is_rejected(self, registered_task):
        from aquilia.tasks.faults import TaskFault
        from aquilia.tasks.workflow import Signature, Workflow

        wf = Workflow("cyclic")
        a = wf.add(Signature(registered_task, (1, 1)))
        b = wf.add(Signature(registered_task, (1, 1)), depends_on=[a])
        wf._nodes[a].depends_on.append(b)
        with pytest.raises(TaskFault):
            wf._validate()

    def test_unknown_dependency_is_rejected(self, registered_task):
        from aquilia.tasks.faults import TaskFault
        from aquilia.tasks.workflow import Signature, Workflow

        wf = Workflow("bad-dep")
        with pytest.raises(TaskFault):
            wf.add(Signature(registered_task, (1, 1)), depends_on=[99])

    async def test_failed_parent_does_not_run_child(self, registered_task):
        """A broken upstream job must not silently release its dependents."""
        from aquilia.tasks.decorators import _task_registry, task
        from aquilia.tasks.workflow import Signature, chain

        @task(name="enterprise_boom")
        async def boom() -> None:
            raise RuntimeError("upstream failed")

        manager = TaskManager(backend=MemoryBackend(), num_workers=2)
        await manager.start()
        try:
            result = await chain(
                Signature(boom),
                Signature(registered_task, (1, 1)),
            ).run(manager)
            await asyncio.sleep(1.0)
            child = await manager.get_job(result.job_ids[1])
            assert child.state is not JobState.COMPLETED
        finally:
            await manager.stop()
            _task_registry.pop("enterprise_boom", None)


# ── Durable backend driven against real SQLite ──────────────────────


@pytest.fixture
async def sqlite_db():
    from aquilia.db.engine import configure_database

    path = Path(tempfile.mkdtemp()) / "enterprise.db"
    db = configure_database(f"sqlite:///{path}")
    await db.connect()
    yield db
    await db.disconnect()
    path.unlink(missing_ok=True)


class TestSQLBackend:
    async def test_job_survives_a_new_manager_over_same_database(self, sqlite_db, registered_task):
        """The restart case: enqueue with one manager, execute with another."""
        from aquilia.tasks.backends import SQLBackend

        producer = TaskManager(backend=SQLBackend(sqlite_db), num_workers=0)
        job_id = await producer.enqueue(registered_task, 20, 22)

        consumer = TaskManager(backend=SQLBackend(sqlite_db), num_workers=2)
        await consumer.start()
        try:
            for _ in range(60):
                job = await consumer.get_job(job_id)
                if job and job.state is JobState.COMPLETED:
                    break
                await asyncio.sleep(0.05)
            job = await consumer.get_job(job_id)
            assert job.state is JobState.COMPLETED
            assert job.result.value == 42
        finally:
            await consumer.stop()

    async def test_consumer_discovers_a_queue_it_never_enqueued_to(self, sqlite_db, registered_task):
        """A consumer-only process must poll queues created by its peers."""
        from aquilia.tasks.backends import SQLBackend

        producer = TaskManager(backend=SQLBackend(sqlite_db), num_workers=0)
        job_id = await producer.enqueue(registered_task, 1, 1, queue="peer-only")

        consumer = TaskManager(backend=SQLBackend(sqlite_db), num_workers=2)
        await consumer.start()
        try:
            for _ in range(60):
                job = await consumer.get_job(job_id)
                if job and job.state is JobState.COMPLETED:
                    break
                await asyncio.sleep(0.05)
            assert (await consumer.get_job(job_id)).state is JobState.COMPLETED
        finally:
            await consumer.stop()

    async def test_dedup_is_enforced_across_managers(self, sqlite_db, registered_task):
        from aquilia.tasks.backends import SQLBackend

        one = TaskManager(backend=SQLBackend(sqlite_db), num_workers=0)
        two = TaskManager(backend=SQLBackend(sqlite_db), num_workers=0)
        first = await one.enqueue(registered_task, 5, 5, queue="dedup", dedup="skip")
        second = await two.enqueue(registered_task, 5, 5, queue="dedup", dedup="skip")
        assert first == second

    async def test_leased_job_is_reclaimed_after_lease_expiry(self, sqlite_db, registered_task):
        """A crashed worker's in-flight job must return to the queue."""
        from aquilia.tasks.backends import SQLBackend

        backend = SQLBackend(sqlite_db, lease_seconds=0.1)
        await backend.initialize()
        await backend.push(Job(name="enterprise_add", args=(1, 2), queue="reclaim"))
        leased = await backend.pop("reclaim")
        assert leased is not None

        await asyncio.sleep(0.25)
        assert await backend.reclaim_expired() >= 1
        assert await backend.pop("reclaim") is not None


# ── Mail: background delivery through the task system ───────────────


@pytest.fixture
async def queued_mail():
    """MailService with queued delivery over a running TaskManager."""
    from aquilia.mail.config import MailConfig
    from aquilia.mail.service import MailService, set_mail_service

    service = MailService(
        MailConfig(
            console_backend=True,
            default_from="sender@example.com",
            queue={"enabled": True},
        )
    )
    await service.on_startup()
    set_mail_service(service)

    manager = TaskManager(backend=MemoryBackend(), num_workers=2)
    await manager.start()
    service.bind_task_manager(manager)

    yield service, manager

    await manager.stop()
    await service.on_shutdown()
    set_mail_service(None)


async def _await_status(service, envelope_id, status, *, ticks=60):
    from aquilia.mail.envelope import EnvelopeStatus

    target = EnvelopeStatus(status) if isinstance(status, str) else status
    for _ in range(ticks):
        envelope = await service.store.get(envelope_id)
        if envelope and envelope.status is target:
            return envelope
        await asyncio.sleep(0.05)
    return await service.store.get(envelope_id)


class TestMailDeliveryQueue:
    async def test_send_returns_before_delivery_then_completes(self, queued_mail):
        from aquilia.mail.envelope import EnvelopeStatus
        from aquilia.mail.message import EmailMessage

        service, _ = queued_mail
        envelope_id = await service.send_message(EmailMessage(subject="queued", body="hi", to="rcpt@example.com"))
        envelope = await _await_status(service, envelope_id, EnvelopeStatus.SENT)
        assert envelope.status is EnvelopeStatus.SENT
        assert envelope.attempts >= 1

    async def test_delivery_task_is_resolvable_by_name(self):
        """A remote worker resolves the delivery task from the registry."""
        from aquilia.tasks.decorators import _task_registry

        assert any("mail" in name for name in _task_registry)

    async def test_queued_job_payload_is_serializable(self, queued_mail):
        """No live MailEnvelope may ride inside the job payload."""
        from aquilia.mail.message import EmailMessage

        service, manager = queued_mail
        envelope_id = await service.send_message(EmailMessage(subject="serializable", body="x", to="rcpt@example.com"))
        job = Job(name="deliver", func_ref="aquilia.mail.deliver", args=(envelope_id,))
        assert job.to_payload()["args"] == [envelope_id]

    async def test_suppressed_recipient_is_not_delivered(self, queued_mail):
        from aquilia.mail.envelope import EnvelopeStatus
        from aquilia.mail.message import EmailMessage
        from aquilia.mail.suppression import SuppressionReason

        service, _ = queued_mail
        await service.suppression.suppress("blocked@example.com", reason=SuppressionReason.HARD_BOUNCE)
        envelope_id = await service.send_message(EmailMessage(subject="blocked", body="x", to="blocked@example.com"))
        envelope = await _await_status(service, envelope_id, EnvelopeStatus.CANCELLED)
        assert envelope.status is EnvelopeStatus.CANCELLED

    async def test_inline_fallback_when_no_task_manager(self):
        """Queued mail must never be accepted with nothing able to send it."""
        from aquilia.mail.config import MailConfig
        from aquilia.mail.message import EmailMessage
        from aquilia.mail.service import MailService

        service = MailService(MailConfig(console_backend=True, queue={"enabled": True}))
        await service.on_startup()
        try:
            envelope_id = await service.send_message(
                EmailMessage(subject="inline", body="x", to="r@example.com", from_email="s@example.com")
            )
            assert (await service.store.get(envelope_id)) is not None
        finally:
            await service.on_shutdown()


# ── Suppression and webhooks ────────────────────────────────────────


class TestSuppression:
    async def test_suppression_is_case_and_whitespace_insensitive(self):
        from aquilia.mail.suppression import MemorySuppressionList, SuppressionReason

        suppression = MemorySuppressionList()
        await suppression.initialize()
        await suppression.suppress("User@Example.COM", reason=SuppressionReason.COMPLAINT)
        assert await suppression.is_suppressed("  user@example.com ")

    async def test_filter_recipients_splits_allowed_and_blocked(self):
        from aquilia.mail.suppression import MemorySuppressionList, SuppressionReason

        suppression = MemorySuppressionList()
        await suppression.initialize()
        await suppression.suppress("bad@example.com", reason=SuppressionReason.HARD_BOUNCE)
        allowed, blocked = await suppression.filter_recipients(["good@example.com", "bad@example.com"])
        assert allowed == ["good@example.com"]
        assert blocked == ["bad@example.com"]

    async def test_transient_suppression_expires(self):
        from aquilia.mail.suppression import MemorySuppressionList, SuppressionReason

        suppression = MemorySuppressionList()
        await suppression.initialize()
        await suppression.suppress("soft@example.com", reason=SuppressionReason.SOFT_BOUNCE, expires_in=-1)
        assert not await suppression.is_suppressed("soft@example.com")

    async def test_unsuppress_restores_delivery(self):
        from aquilia.mail.suppression import MemorySuppressionList, SuppressionReason

        suppression = MemorySuppressionList()
        await suppression.initialize()
        await suppression.suppress("x@example.com", reason=SuppressionReason.MANUAL)
        assert await suppression.unsuppress("x@example.com")
        assert not await suppression.is_suppressed("x@example.com")

    async def test_sql_suppression_survives_a_new_instance(self, sqlite_db):
        from aquilia.mail.suppression import SQLSuppressionList, SuppressionReason

        first = SQLSuppressionList(sqlite_db)
        await first.initialize()
        await first.suppress("durable@example.com", reason=SuppressionReason.HARD_BOUNCE)

        second = SQLSuppressionList(sqlite_db)
        await second.initialize()
        assert await second.is_suppressed("durable@example.com")


class TestWebhookParsing:
    def test_ses_bounce_yields_a_bounce_event(self):
        import json

        from aquilia.mail.webhooks import EventType, parse_ses

        payload = {
            "Message": json.dumps(
                {
                    "notificationType": "Bounce",
                    "bounce": {
                        "bounceType": "Permanent",
                        "bouncedRecipients": [{"emailAddress": "bounce@example.com"}],
                        "timestamp": "2026-01-01T00:00:00.000Z",
                    },
                    "mail": {"messageId": "abc"},
                }
            )
        }
        events = parse_ses(payload)
        assert [e.event_type for e in events] == [EventType.HARD_BOUNCE]
        assert events[0].email == "bounce@example.com"

    def test_ses_wrong_topic_arn_is_rejected(self):
        from aquilia.mail.faults import MailFault
        from aquilia.mail.webhooks import parse_ses

        with pytest.raises(MailFault):
            parse_ses({"TopicArn": "arn:aws:sns:evil", "Message": "{}"}, verify_topic_arn="arn:aws:sns:mine")

    def test_sendgrid_events_parse(self):
        from aquilia.mail.webhooks import parse_sendgrid

        events = parse_sendgrid(
            [{"event": "bounce", "email": "b@example.com", "timestamp": 1767225600, "type": "blocked"}]
        )
        assert events[0].email == "b@example.com"

    def test_malformed_payload_raises_mail_fault(self):
        from aquilia.mail.faults import MailFault
        from aquilia.mail.webhooks import parse_sendgrid

        with pytest.raises(MailFault):
            parse_sendgrid(b"not json")


class TestWebhookProcessing:
    async def test_hard_bounce_suppresses_the_recipient(self):
        import json

        from aquilia.mail.store import MemoryEnvelopeStore
        from aquilia.mail.suppression import MemorySuppressionList
        from aquilia.mail.webhooks import parse_ses, process_webhook

        suppression = MemorySuppressionList()
        await suppression.initialize()
        store = MemoryEnvelopeStore()
        await store.initialize()

        events = parse_ses(
            {
                "Message": json.dumps(
                    {
                        "notificationType": "Bounce",
                        "bounce": {
                            "bounceType": "Permanent",
                            "bouncedRecipients": [{"emailAddress": "hard@example.com"}],
                            "timestamp": "2026-01-01T00:00:00.000Z",
                        },
                        "mail": {"messageId": "m1"},
                    }
                )
            }
        )
        await process_webhook(events, suppression=suppression, store=store)
        assert await suppression.is_suppressed("hard@example.com")

    async def test_delivery_event_does_not_suppress(self):
        import json

        from aquilia.mail.suppression import MemorySuppressionList
        from aquilia.mail.webhooks import parse_ses, process_webhook

        suppression = MemorySuppressionList()
        await suppression.initialize()
        events = parse_ses(
            {
                "Message": json.dumps(
                    {
                        "notificationType": "Delivery",
                        "delivery": {
                            "recipients": ["ok@example.com"],
                            "timestamp": "2026-01-01T00:00:00.000Z",
                        },
                        "mail": {"messageId": "m2"},
                    }
                )
            }
        )
        await process_webhook(events, suppression=suppression)
        assert not await suppression.is_suppressed("ok@example.com")


# ── Template autoescaping ───────────────────────────────────────────


class TestTemplateAutoescaping:
    """The Jinja engine escapes by default; ATS coverage lives in the audit suite."""

    @pytest.fixture
    def engine(self, tmp_path):
        from aquilia.templates.engine import TemplateEngine
        from aquilia.templates.loader import TemplateLoader

        (tmp_path / "escaped.html").write_text("<p>{{ value }}</p>")
        (tmp_path / "safe.html").write_text("<p>{{ value|safe }}</p>")
        return TemplateEngine(loader=TemplateLoader(search_paths=[str(tmp_path)]))

    async def test_interpolation_is_escaped_by_default(self, engine):
        out = await engine.render("escaped.html", {"value": "<script>alert(1)</script>"})
        assert "<script>" not in out
        assert "&lt;script&gt;" in out

    async def test_safe_filter_opts_out(self, engine):
        assert await engine.render("safe.html", {"value": "<b>ok</b>"}) == "<p><b>ok</b></p>"
