"""
Regression tests for the task & mail subsystem audit findings.

Each test maps to a specific audited defect:

Task system
    A2-01  Cron day-of-week used Python's Monday=0 instead of cron's Sunday=0.
    A2-02  ``MemoryBackend.pop()`` returned ``None`` on the first not-yet-due
           job, starving every ready job behind it.
    A2-03  ``TaskManager.stop(timeout=...)`` ignored ``timeout`` and could
           hang forever on a task that swallows ``CancelledError``.
    A2-05  ``scheduler_tick`` and ``dead_letter_max`` were dropped between
           config and runtime.
    A2-06  ``Worker`` duplicated the manager's loop and never counted real
           job failures.

Mail system
    B2-01  Envelope retry fields were modelled but never used.
    B2-02  ``EmailMessage.send()`` called ``run_until_complete`` inside a
           running loop.
    B2-03  ``*_env`` credential fields were never read from the environment.
    B2-04  Template interpolation performed no HTML escaping.
    B2-05  Unsupported filters / control flow were silently dropped.
    B2-06  ``rate_limit_per_min`` was never enforced.
    B2-07  DKIM signing and PII redaction were docstring-only.
    B2-08  MIME construction was duplicated across SMTP and SES.
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta, timezone

import pytest

from aquilia.mail.config import MailConfig, ProviderConfig, SecurityConfig
from aquilia.mail.envelope import MailEnvelope
from aquilia.mail.faults import MailConfigFault, MailSendFault, MailTemplateFault
from aquilia.mail.message import EmailMessage, TemplateMessage
from aquilia.mail.mime import build_mime_message, extract_domain
from aquilia.mail.providers import ProviderResult, ProviderResultStatus
from aquilia.mail.providers.ses import SESProvider
from aquilia.mail.providers.smtp import SMTPProvider
from aquilia.mail.redaction import redact_email, redact_pii
from aquilia.mail.service import MailService, _TokenBucket, set_mail_service
from aquilia.mail.template import register_filter, render_string
from aquilia.tasks import MemoryBackend, TaskManager, Worker, cron, task
from aquilia.tasks.faults import TaskScheduleFault
from aquilia.tasks.job import Job, JobState, Priority

# ════════════════════════════════════════════════════════════════════
# A2-01 — Cron day-of-week convention
# ════════════════════════════════════════════════════════════════════


class TestCronDayOfWeek:
    """DOW must follow cron convention (0 = Sunday), not Python's weekday()."""

    # 2026-07-26 is a Sunday; 07-27 Monday ... 08-01 Saturday.
    SUNDAY = datetime(2026, 7, 26, 2, 30, tzinfo=timezone.utc)
    MONDAY = datetime(2026, 7, 27, 2, 30, tzinfo=timezone.utc)
    TUESDAY = datetime(2026, 7, 28, 2, 30, tzinfo=timezone.utc)
    SATURDAY = datetime(2026, 8, 1, 2, 30, tzinfo=timezone.utc)

    def test_dow_1_is_monday(self):
        schedule = cron("30 2 * * 1")
        assert schedule.matches(self.MONDAY)
        assert not schedule.matches(self.TUESDAY)
        assert not schedule.matches(self.SUNDAY)

    def test_dow_0_is_sunday(self):
        schedule = cron("30 2 * * 0")
        assert schedule.matches(self.SUNDAY)
        assert not schedule.matches(self.MONDAY)

    def test_dow_7_also_sunday(self):
        """Standard cron accepts both 0 and 7 for Sunday."""
        schedule = cron("30 2 * * 7")
        assert schedule.matches(self.SUNDAY)
        assert not schedule.matches(self.MONDAY)

    def test_dow_6_is_saturday(self):
        schedule = cron("30 2 * * 6")
        assert schedule.matches(self.SATURDAY)
        assert not schedule.matches(self.SUNDAY)

    def test_weekday_range_excludes_weekend(self):
        schedule = cron("30 2 * * 1-5")
        assert schedule.matches(self.MONDAY)
        assert schedule.matches(self.TUESDAY)
        assert not schedule.matches(self.SATURDAY)
        assert not schedule.matches(self.SUNDAY)

    def test_next_run_lands_on_correct_weekday(self):
        schedule = cron("30 2 * * 1")
        nxt = schedule.next_run(datetime(2026, 7, 26, 0, 0, tzinfo=timezone.utc))
        assert nxt.isoweekday() == 1  # Monday
        assert (nxt.hour, nxt.minute) == (2, 30)

    def test_out_of_range_field_raises(self):
        with pytest.raises(TaskScheduleFault):
            cron("70 2 * * 1")
        with pytest.raises(TaskScheduleFault):
            cron("30 2 * 13 1")
        with pytest.raises(TaskScheduleFault):
            cron("30 2 * * 8")

    def test_non_numeric_field_raises(self):
        with pytest.raises(TaskScheduleFault):
            cron("30 2 * * MON")

    def test_zero_step_raises(self):
        with pytest.raises(TaskScheduleFault):
            cron("*/0 * * * *")

    def test_wrong_field_count_raises(self):
        with pytest.raises(TaskScheduleFault):
            cron("* * * *")


# ════════════════════════════════════════════════════════════════════
# A2-02 — MemoryBackend.pop() head-of-line blocking
# ════════════════════════════════════════════════════════════════════


def _job(name: str, *, priority: Priority = Priority.NORMAL, delay: float | None = None) -> Job:
    return Job(
        name=name,
        queue="default",
        priority=priority,
        func_ref=f"tests:{name}",
        state=JobState.SCHEDULED if delay else JobState.PENDING,
        scheduled_at=(datetime.now(timezone.utc) + timedelta(seconds=delay)) if delay else None,
    )


class TestMemoryBackendPop:
    """A not-yet-due job must be skipped, never block the queue."""

    async def test_delayed_high_priority_does_not_starve_ready_job(self):
        backend = MemoryBackend()
        await backend.push(_job("later", priority=Priority.CRITICAL, delay=300))
        await backend.push(_job("now", priority=Priority.LOW))

        popped = await backend.pop("default")
        assert popped is not None
        assert popped.name == "now"

    async def test_deferred_job_is_pushed_back(self):
        backend = MemoryBackend()
        await backend.push(_job("later", priority=Priority.CRITICAL, delay=300))
        await backend.push(_job("now", priority=Priority.LOW))

        assert (await backend.pop("default")).name == "now"
        # The deferred job survived the scan and is still queued.
        assert len(backend._queues["default"]) == 1

    async def test_returns_none_when_all_jobs_deferred(self):
        backend = MemoryBackend()
        await backend.push(_job("a", delay=300))
        await backend.push(_job("b", delay=300))
        assert await backend.pop("default") is None
        assert len(backend._queues["default"]) == 2

    async def test_priority_order_preserved_among_ready_jobs(self):
        backend = MemoryBackend()
        await backend.push(_job("low", priority=Priority.LOW))
        await backend.push(_job("critical", priority=Priority.CRITICAL))
        assert (await backend.pop("default")).name == "critical"
        assert (await backend.pop("default")).name == "low"

    async def test_terminal_jobs_skipped(self):
        backend = MemoryBackend()
        done = _job("done", priority=Priority.CRITICAL)
        done.state = JobState.COMPLETED
        await backend.push(done)
        await backend.push(_job("pending", priority=Priority.LOW))
        assert (await backend.pop("default")).name == "pending"

    async def test_empty_queue_returns_none(self):
        backend = MemoryBackend()
        assert await backend.pop("nonexistent") is None


# ════════════════════════════════════════════════════════════════════
# A2-03 / A2-05 — shutdown timeout & dropped config
# ════════════════════════════════════════════════════════════════════


class TestManagerLifecycle:
    async def test_dead_letter_max_is_configurable(self):
        backend = MemoryBackend(dead_letter_max=3)
        assert backend.dead_letter_max == 3
        assert backend._dead_letter.maxlen == 3

    async def test_dead_letter_evicts_oldest_beyond_cap(self):
        backend = MemoryBackend(dead_letter_max=2)
        for i in range(4):
            j = _job(f"j{i}")
            j.state = JobState.DEAD
            await backend.update(j)
        assert len(backend._dead_letter) == 2
        assert [j.name for j in backend._dead_letter] == ["j2", "j3"]

    async def test_scheduler_tick_is_stored(self):
        manager = TaskManager(num_workers=0, scheduler_tick=1.5)
        assert manager.scheduler_tick == 1.5

    async def test_configured_defaults_reach_a_plain_callable_job(self):
        """
        Part C: config fields must not be dropped between integration and job.

        ``default_timeout`` / retry defaults were previously hardcoded inside
        ``enqueue``, so ``Integration.tasks(default_timeout=...)`` had no
        effect on any callable enqueued without a ``@task`` decorator.
        """
        manager = TaskManager(
            num_workers=0,
            default_timeout=12.5,
            default_max_retries=7,
            default_retry_delay=2.5,
            default_retry_backoff=3.0,
            default_retry_max_delay=99.0,
        )

        async def plain() -> None:
            return None

        job_id = await manager.enqueue(plain)
        job = await manager.get_job(job_id)

        assert job.timeout == 12.5
        assert job.max_retries == 7
        assert job.retry_delay == 2.5
        assert job.retry_backoff == 3.0
        assert job.retry_max_delay == 99.0

    async def test_explicit_enqueue_args_override_manager_defaults(self):
        manager = TaskManager(num_workers=0, default_timeout=12.5, default_max_retries=7)

        async def plain() -> None:
            return None

        job = await manager.get_job(await manager.enqueue(plain, timeout=1.0, max_retries=0))
        assert job.timeout == 1.0
        assert job.max_retries == 0

    async def test_decorator_values_win_over_manager_defaults(self):
        manager = TaskManager(num_workers=0, default_timeout=12.5, default_max_retries=7)

        @task(name="_audit_defaults_task", timeout=3.0, max_retries=1)
        async def decorated() -> None:
            return None

        job = await manager.get_job(await manager.enqueue(decorated))
        assert job.timeout == 3.0
        assert job.max_retries == 1

    async def test_stop_honours_timeout_on_uncancellable_task(self):
        """stop() must return even when a worker refuses to unwind."""
        manager = TaskManager(num_workers=0)

        async def stubborn() -> None:
            while True:
                try:
                    await asyncio.sleep(3600)
                except asyncio.CancelledError:
                    continue  # deliberately swallows cancellation

        manager._running = True
        manager._workers.append(asyncio.create_task(stubborn(), name="stubborn"))

        started = asyncio.get_running_loop().time()
        await manager.stop(timeout=0.2)
        elapsed = asyncio.get_running_loop().time() - started

        assert elapsed < 2.0
        assert manager._workers == []

    async def test_stop_is_safe_with_no_workers(self):
        manager = TaskManager(num_workers=0)
        await manager.stop(timeout=0.1)
        assert manager.is_running is False

    async def test_start_stop_roundtrip(self):
        manager = TaskManager(num_workers=1, scheduler_tick=60.0)
        await manager.start()
        assert manager.is_running
        await manager.stop(timeout=2.0)
        assert not manager.is_running
        assert manager._cleanup_task is None
        assert manager._scheduler_task is None


# ════════════════════════════════════════════════════════════════════
# Part C — config actually reaches the runtime (server wiring)
# ════════════════════════════════════════════════════════════════════


def _server_with_tasks(**tasks_config):
    from aquilia.config import ConfigLoader
    from aquilia.manifest import AppManifest
    from aquilia.server import AquiliaServer
    from aquilia.workspace import Workspace

    config = Workspace("tasks-ws").to_dict()
    config.setdefault("integrations", {})["tasks"] = {"enabled": True, **tasks_config}

    loader = ConfigLoader()
    loader.config_data = config
    loader._build_apps_namespace()

    return AquiliaServer(manifests=[AppManifest(name="app", version="0.0.1")], config=loader)


class TestServerTaskWiring:
    """Every ``TasksIntegration`` field must survive the trip to runtime."""

    def test_scheduler_tick_reaches_the_manager(self):
        server = _server_with_tasks(scheduler_tick=1.25)
        assert server._task_manager is not None
        assert server._task_manager.scheduler_tick == 1.25

    def test_dead_letter_max_reaches_the_backend(self):
        server = _server_with_tasks(dead_letter_max=4242)
        assert server._task_manager.backend.dead_letter_max == 4242

    def test_retry_and_timeout_defaults_reach_the_manager(self):
        server = _server_with_tasks(
            default_timeout=11.0,
            max_retries=9,
            retry_delay=4.0,
            retry_backoff=5.0,
            retry_max_delay=77.0,
        )
        manager = server._task_manager
        assert manager.default_timeout == 11.0
        assert manager.default_max_retries == 9
        assert manager.default_retry_delay == 4.0
        assert manager.default_retry_backoff == 5.0
        assert manager.default_retry_max_delay == 77.0

    def test_auto_start_flag_is_recorded(self):
        assert _server_with_tasks(auto_start=False)._task_auto_start is False
        assert _server_with_tasks(auto_start=True)._task_auto_start is True

    def test_redis_backend_is_selected_without_warning(self, caplog):
        """``backend="redis"`` builds a RedisBackend; it no longer degrades."""
        from aquilia.tasks.backends import RedisBackend

        with caplog.at_level("WARNING", logger="aquilia.server"):
            server = _server_with_tasks(backend="redis")
        assert isinstance(server._task_manager.backend, RedisBackend)
        assert "not implemented" not in caplog.text.lower()

    def test_unknown_backend_warns_and_falls_back(self, caplog):
        with caplog.at_level("WARNING", logger="aquilia.server"):
            server = _server_with_tasks(backend="rabbitmq")
        assert isinstance(server._task_manager.backend, MemoryBackend)
        assert "rabbitmq" in caplog.text.lower()

    def test_memory_backend_does_not_warn(self, caplog):
        with caplog.at_level("WARNING", logger="aquilia.server"):
            server = _server_with_tasks(backend="memory")
        assert isinstance(server._task_manager.backend, MemoryBackend)
        assert "not implemented" not in caplog.text.lower()

    def test_num_workers_and_queue_reach_the_manager(self):
        server = _server_with_tasks(num_workers=6, default_queue="jobs")
        assert server._task_manager.num_workers == 6
        assert server._task_manager.default_queue == "jobs"


# ════════════════════════════════════════════════════════════════════
# A2-06 — Worker delegation & jobs_failed semantics
# ════════════════════════════════════════════════════════════════════


class TestWorkerMetrics:
    async def test_drain_once_returns_none_when_idle(self):
        manager = TaskManager(num_workers=0)
        assert await manager.drain_once("t") is None

    async def test_drain_once_executes_and_returns_job(self):
        manager = TaskManager(num_workers=0)
        ran: list[str] = []

        async def ok() -> str:
            ran.append("yes")
            return "done"

        await manager.enqueue(ok)
        job = await manager.drain_once("t")
        assert ran == ["yes"]
        assert job is not None
        assert job.state is JobState.COMPLETED

    async def test_worker_counts_failed_jobs(self):
        """jobs_failed must reflect real job failures, not just loop errors."""
        manager = TaskManager(num_workers=0)

        async def boom() -> None:
            raise ValueError("nope")

        await manager.enqueue(boom, max_retries=0)

        worker = Worker(manager, name="w", poll_interval=0.01)
        await worker.start()
        for _ in range(200):
            if worker.stats["jobs_processed"]:
                break
            await asyncio.sleep(0.01)
        await worker.stop()

        assert worker.stats["jobs_processed"] >= 1
        assert worker.stats["jobs_failed"] >= 1

    async def test_worker_does_not_count_successes_as_failures(self):
        manager = TaskManager(num_workers=0)

        async def fine() -> int:
            return 1

        await manager.enqueue(fine)

        worker = Worker(manager, name="w", poll_interval=0.01)
        await worker.start()
        for _ in range(200):
            if worker.stats["jobs_processed"]:
                break
            await asyncio.sleep(0.01)
        await worker.stop()

        assert worker.stats["jobs_processed"] >= 1
        assert worker.stats["jobs_failed"] == 0

    async def test_worker_restart_is_idempotent(self):
        manager = TaskManager(num_workers=0)
        worker = Worker(manager, name="w", poll_interval=0.01)
        await worker.start()
        await worker.start()  # no-op
        assert worker.is_running
        await worker.stop()
        assert not worker.is_running


# ════════════════════════════════════════════════════════════════════
# B2-04 / B2-05 — Template escaping and loud failures
# ════════════════════════════════════════════════════════════════════


class TestTemplateEscaping:
    def test_interpolation_is_html_escaped(self):
        out = render_string("Hi << name >>", {"name": "<script>alert(1)</script>"})
        assert "<script>" not in out
        assert "&lt;script&gt;" in out

    def test_quotes_are_escaped(self):
        out = render_string("<a title='<< t >>'>x</a>", {"t": "a\" onload='x'"})
        assert "&quot;" in out
        assert "&#x27;" in out

    def test_safe_filter_opts_out(self):
        out = render_string("<< body | safe >>", {"body": "<p>ok</p>"})
        assert out == "<p>ok</p>"

    def test_autoescape_false_skips_escaping(self):
        out = render_string("<< name >>", {"name": "A & B"}, autoescape=False)
        assert out == "A & B"

    def test_missing_value_renders_empty(self):
        assert render_string("[<< nope >>]", {}) == "[]"

    def test_dotted_lookup(self):
        assert render_string("<< user.name >>", {"user": {"name": "Asha"}}) == "Asha"


class TestTemplateFilters:
    def test_currency_filter_applied(self):
        assert render_string("<< price | currency('USD') >>", {"price": 12.5}) == "USD 12.50"

    def test_title_filter_applied(self):
        assert render_string("<< n | title >>", {"n": "asha rao"}) == "Asha Rao"

    def test_truncate_filter_applied(self):
        out = render_string("<< b | truncate(5) >>", {"b": "abcdefghij"})
        assert out.startswith("abcde")

    def test_chained_filters(self):
        assert render_string("<< n | trim | upper >>", {"n": "  hi  "}) == "HI"

    def test_pipe_inside_string_literal_not_a_filter_split(self):
        out = render_string("<< p | currency('A|B') >>", {"p": 1})
        assert out == "A|B 1.00"

    def test_unknown_filter_raises(self):
        with pytest.raises(MailTemplateFault):
            render_string("<< n | bogus >>", {"n": "x"})

    def test_bad_filter_argument_raises(self):
        with pytest.raises(MailTemplateFault):
            render_string("<< n | truncate(zzz) >>", {"n": "x"})

    def test_control_flow_tag_raises(self):
        with pytest.raises(MailTemplateFault):
            render_string("[[% if cond %]]x[[% endif %]]", {})

    def test_duplicate_filter_registration_raises(self):
        with pytest.raises(MailTemplateFault):
            register_filter("upper", lambda v: v)

    def test_custom_filter_registration(self):
        register_filter("_test_shout", lambda v: f"{v}!")
        assert render_string("<< n | _test_shout >>", {"n": "hi"}) == "hi!"


# ════════════════════════════════════════════════════════════════════
# B2-03 — Credential env-var resolution
# ════════════════════════════════════════════════════════════════════


class TestCredentialResolution:
    def test_password_env_is_read(self, monkeypatch):
        monkeypatch.setenv("TEST_SMTP_PASS", "s3cr3t")
        svc = MailService(MailConfig())
        pc = ProviderConfig(
            {
                "name": "smtp1",
                "type": "smtp",
                "host": "localhost",
                "auth": {"method": "plain", "username": "u", "password_env": "TEST_SMTP_PASS"},
            }
        )
        provider = svc._create_provider(pc)
        assert provider.password == "s3cr3t"
        assert provider.username == "u"

    def test_literal_password_wins_over_env(self, monkeypatch):
        monkeypatch.setenv("TEST_SMTP_PASS", "from-env")
        svc = MailService(MailConfig())
        pc = ProviderConfig(
            {
                "name": "smtp1",
                "type": "smtp",
                "host": "localhost",
                "auth": {"method": "plain", "username": "u", "password": "literal", "password_env": "TEST_SMTP_PASS"},
            }
        )
        assert svc._create_provider(pc).password == "literal"

    def test_missing_env_var_yields_none_and_warns(self, caplog):
        os.environ.pop("TEST_ABSENT_PASS", None)
        svc = MailService(MailConfig())
        pc = ProviderConfig(
            {
                "name": "smtp1",
                "type": "smtp",
                "host": "localhost",
                "auth": {"method": "plain", "username": "u", "password_env": "TEST_ABSENT_PASS"},
            }
        )
        with caplog.at_level("WARNING", logger="aquilia.mail"):
            provider = svc._create_provider(pc)
        assert provider.password is None
        assert "TEST_ABSENT_PASS" in caplog.text

    def test_api_key_env_is_read(self, monkeypatch):
        monkeypatch.setenv("TEST_SG_KEY", "SG.key")
        svc = MailService(MailConfig())
        pc = ProviderConfig(
            {
                "name": "sg",
                "type": "sendgrid",
                "auth": {"method": "api_key", "api_key_env": "TEST_SG_KEY"},
            }
        )
        assert svc._create_provider(pc).api_key == "SG.key"

    def test_aws_credential_envs_are_read(self, monkeypatch):
        monkeypatch.setenv("TEST_AWS_ID", "AKIA")
        monkeypatch.setenv("TEST_AWS_SECRET", "shhh")
        svc = MailService(MailConfig())
        pc = ProviderConfig(
            {
                "name": "ses",
                "type": "ses",
                "auth": {
                    "method": "api_key",
                    "aws_access_key_id_env": "TEST_AWS_ID",
                    "aws_secret_access_key_env": "TEST_AWS_SECRET",
                    "aws_region": "eu-west-1",
                },
            }
        )
        provider = svc._create_provider(pc)
        assert provider.aws_access_key_id == "AKIA"
        assert provider.aws_secret_access_key == "shhh"
        assert provider.region == "eu-west-1"

    def test_oauth2_token_env_reaches_smtp_provider(self, monkeypatch):
        monkeypatch.setenv("TEST_OAUTH_TOKEN", "ya29.token")
        svc = MailService(MailConfig())
        pc = ProviderConfig(
            {
                "name": "gmail",
                "type": "smtp",
                "host": "smtp.gmail.com",
                "auth": {
                    "method": "oauth2",
                    "username": "u@gmail.com",
                    "access_token_env": "TEST_OAUTH_TOKEN",
                },
            }
        )
        assert svc._create_provider(pc).oauth2_token == "ya29.token"

    def test_non_oauth2_auth_yields_no_token(self):
        svc = MailService(MailConfig())
        assert svc._resolve_oauth2_token({"method": "plain", "access_token": "x"}) is None


class TestXOAuth2:
    def test_xoauth2_string_format(self):
        provider = SMTPProvider(name="g", username="u@x.com", oauth2_token="tok")
        import base64

        decoded = base64.b64decode(provider._xoauth2_string()).decode()
        assert decoded == "user=u@x.com\x01auth=Bearer tok\x01\x01"

    def test_xoauth2_requires_username(self):
        provider = SMTPProvider(name="g", username=None, oauth2_token="tok")
        with pytest.raises(ValueError):
            provider._xoauth2_string()


# ════════════════════════════════════════════════════════════════════
# B2-02 — Sync send inside a running loop
# ════════════════════════════════════════════════════════════════════


class TestSyncSendGuard:
    async def test_send_raises_inside_running_loop(self):
        svc = MailService(MailConfig(console_backend=True))
        set_mail_service(svc)
        try:
            msg = EmailMessage(subject="x", body="y", to="a@b.co")
            with pytest.raises(MailConfigFault) as exc:
                msg.send()
            assert "asend" in str(exc.value)
        finally:
            set_mail_service(None)

    async def test_fail_silently_does_not_mask_the_guard(self):
        """The guard is a programming error, not a delivery failure."""
        svc = MailService(MailConfig(console_backend=True))
        set_mail_service(svc)
        try:
            with pytest.raises(MailConfigFault):
                EmailMessage(subject="x", body="y", to="a@b.co").send(fail_silently=True)
        finally:
            set_mail_service(None)

    async def test_asend_works_inside_loop(self):
        svc = MailService(MailConfig(console_backend=True))
        await svc.on_startup()
        set_mail_service(svc)
        try:
            envelope_id = await EmailMessage(subject="x", body="y", to="a@b.co").asend()
            assert envelope_id
        finally:
            set_mail_service(None)
            await svc.on_shutdown()


# ════════════════════════════════════════════════════════════════════
# B2-06 — Rate limiting
# ════════════════════════════════════════════════════════════════════


class _RecordingProvider:
    """Minimal provider that records sends and returns a scripted result."""

    supports_batching = False
    max_batch_size = 1

    def __init__(
        self,
        name: str = "rec",
        *,
        status: ProviderResultStatus = ProviderResultStatus.SUCCESS,
        priority: int = 50,
        rate_limit_per_min: int = 0,
        retry_after: float | None = None,
    ) -> None:
        self.name = name
        self.status = status
        self.priority = priority
        self.rate_limit_per_min = rate_limit_per_min
        self.retry_after = retry_after
        self.sent: list[MailEnvelope] = []

    async def initialize(self) -> None:
        return None

    async def shutdown(self) -> None:
        return None

    async def health_check(self) -> bool:
        return True

    async def send(self, envelope: MailEnvelope) -> ProviderResult:
        self.sent.append(envelope)
        return ProviderResult(
            status=self.status,
            provider_message_id="mid" if self.status is ProviderResultStatus.SUCCESS else None,
            error_message=None if self.status is ProviderResultStatus.SUCCESS else "scripted failure",
            retry_after=self.retry_after,
        )


def _service_with(*providers: _RecordingProvider, config: MailConfig | None = None) -> MailService:
    svc = MailService(config or MailConfig())
    for p in providers:
        svc._providers[p.name] = p
    svc._started = True
    return svc


class TestTokenBucket:
    def test_disabled_bucket_always_allows(self):
        bucket = _TokenBucket(0)
        assert not bucket.enabled
        assert all(bucket.acquire() for _ in range(1000))

    def test_capacity_then_exhaustion(self):
        bucket = _TokenBucket(3)
        assert [bucket.acquire() for _ in range(3)] == [True, True, True]
        assert bucket.acquire() is False

    def test_retry_after_positive_when_empty(self):
        bucket = _TokenBucket(60)
        for _ in range(60):
            bucket.acquire()
        assert bucket.retry_after() > 0

    def test_retry_after_zero_when_tokens_available(self):
        assert _TokenBucket(60).retry_after() == 0.0


class TestRateLimitEnforcement:
    async def test_over_rate_provider_is_skipped_for_fallback(self):
        limited = _RecordingProvider("limited", priority=1, rate_limit_per_min=1)
        backup = _RecordingProvider("backup", priority=2)
        svc = _service_with(limited, backup)

        await svc.send_message(EmailMessage(subject="1", body="b", to="a@b.co"))
        await svc.send_message(EmailMessage(subject="2", body="b", to="a@b.co"))

        assert len(limited.sent) == 1
        assert len(backup.sent) == 1

    async def test_unthrottled_provider_takes_every_send(self):
        p = _RecordingProvider("p", rate_limit_per_min=0)
        svc = _service_with(p)
        for i in range(5):
            await svc.send_message(EmailMessage(subject=str(i), body="b", to="a@b.co"))
        assert len(p.sent) == 5

    async def test_all_providers_limited_raises_and_leaves_envelope_failed(self):
        p = _RecordingProvider("p", rate_limit_per_min=1)
        svc = _service_with(p)
        await svc.send_message(EmailMessage(subject="1", body="b", to="a@b.co"))
        with pytest.raises(MailSendFault):
            await svc.send_message(EmailMessage(subject="2", body="b", to="a@b.co"))


# ════════════════════════════════════════════════════════════════════
# B2-01 — Retry actually happens
# ════════════════════════════════════════════════════════════════════


class TestRetryPipeline:
    async def test_attempts_increment_on_dispatch(self):
        p = _RecordingProvider("p")
        svc = _service_with(p)
        envelope = MailEnvelope(from_email="f@x.co", to=["a@b.co"], subject="s", body_text="b")
        await svc.send_envelope(envelope)
        assert envelope.attempts == 1
        assert envelope.last_attempt_at is not None

    async def test_transient_failure_schedules_retry_via_task_manager(self):
        p = _RecordingProvider("p", status=ProviderResultStatus.TRANSIENT_FAILURE, retry_after=0.01)
        svc = _service_with(p)
        manager = TaskManager(num_workers=0)
        await manager.start()
        svc.bind_task_manager(manager)
        set_mail_service(svc)
        try:
            envelope = MailEnvelope(from_email="f@x.co", to=["a@b.co"], subject="s", body_text="b")
            await svc.send_envelope(envelope)  # must NOT raise -- retry queued
            assert envelope.next_attempt_at is not None
            jobs = await manager.list_jobs()
            assert any(j.queue == svc.retry_queue for j in jobs)
        finally:
            set_mail_service(None)
            await manager.stop(timeout=1.0)

    async def test_retry_budget_exhaustion_raises(self):
        p = _RecordingProvider("p", status=ProviderResultStatus.TRANSIENT_FAILURE)
        svc = _service_with(p)
        manager = TaskManager(num_workers=0)
        await manager.start()
        svc.bind_task_manager(manager)
        try:
            envelope = MailEnvelope(
                from_email="f@x.co",
                to=["a@b.co"],
                subject="s",
                body_text="b",
                attempts=5,
                max_attempts=5,
            )
            with pytest.raises(MailSendFault):
                await svc.send_envelope(envelope)
        finally:
            await manager.stop(timeout=1.0)

    async def test_no_task_manager_means_no_retry(self):
        p = _RecordingProvider("p", status=ProviderResultStatus.TRANSIENT_FAILURE)
        svc = _service_with(p)
        envelope = MailEnvelope(from_email="f@x.co", to=["a@b.co"], subject="s", body_text="b")
        with pytest.raises(MailSendFault):
            await svc.send_envelope(envelope)

    async def test_permanent_failure_does_not_try_other_providers(self):
        bad = _RecordingProvider("bad", status=ProviderResultStatus.PERMANENT_FAILURE, priority=1)
        backup = _RecordingProvider("backup", priority=2)
        svc = _service_with(bad, backup)
        with pytest.raises(MailSendFault):
            await svc.send_message(EmailMessage(subject="s", body="b", to="a@b.co"))
        assert len(bad.sent) == 1
        assert backup.sent == []

    async def test_transient_failure_fails_over_to_next_provider(self):
        flaky = _RecordingProvider("flaky", status=ProviderResultStatus.TRANSIENT_FAILURE, priority=1)
        backup = _RecordingProvider("backup", priority=2)
        svc = _service_with(flaky, backup)
        await svc.send_message(EmailMessage(subject="s", body="b", to="a@b.co"))
        assert len(flaky.sent) == 1
        assert len(backup.sent) == 1

    async def test_retry_delay_prefers_provider_hint(self):
        svc = _service_with(_RecordingProvider("p"))
        envelope = MailEnvelope(attempts=1)
        assert svc._retry_delay(envelope, 42.0) == 42.0

    async def test_retry_delay_backoff_grows_and_is_capped(self):
        cfg = MailConfig(retry={"base_delay": 1.0, "max_delay": 8.0, "jitter": False})
        svc = _service_with(_RecordingProvider("p"), config=cfg)
        assert svc._retry_delay(MailEnvelope(attempts=1), None) == 1.0
        assert svc._retry_delay(MailEnvelope(attempts=3), None) == 4.0
        assert svc._retry_delay(MailEnvelope(attempts=9), None) == 8.0


# ════════════════════════════════════════════════════════════════════
# B2-08 — Shared MIME construction, attachment payloads
# ════════════════════════════════════════════════════════════════════


class TestSharedMime:
    def test_smtp_and_ses_produce_the_same_structure(self):
        envelope = MailEnvelope(
            from_email="f@x.co",
            to=["a@b.co"],
            subject="s",
            body_text="text",
            body_html="<p>html</p>",
        )
        smtp_msg = SMTPProvider(name="s")._build_mime_message(envelope)
        shared = build_mime_message(envelope)
        assert smtp_msg.get_content_type() == shared.get_content_type()
        assert [p.get_content_type() for p in smtp_msg.walk()] == [p.get_content_type() for p in shared.walk()]

    def test_ses_raw_message_uses_shared_builder(self):
        envelope = MailEnvelope(from_email="f@x.co", to=["a@b.co"], subject="s", body_text="t")
        raw = SESProvider(name="ses")._build_raw_message(envelope)
        assert b"Subject: s" in raw
        assert b"X-Aquilia-Envelope-ID" in raw

    def test_attachment_bytes_reach_the_mime_part(self):
        msg = EmailMessage(subject="s", body="b", to="a@b.co")
        msg.attach("hello.txt", b"payload-bytes", "text/plain")
        envelope, blobs = msg.build_envelope()
        for digest, content in blobs.items():
            envelope.metadata[f"blob:{digest}"] = content

        mime = build_mime_message(envelope)
        payloads = [p.get_payload(decode=True) for p in mime.walk() if p.get_filename() == "hello.txt"]
        assert payloads == [b"payload-bytes"]

    async def test_service_populates_attachment_blobs(self):
        p = _RecordingProvider("p")
        svc = _service_with(p)
        msg = EmailMessage(subject="s", body="b", to="a@b.co")
        msg.attach("f.bin", b"\x00\x01", "application/octet-stream")
        await svc.send_message(msg)
        sent = p.sent[0]
        assert any(k.startswith("blob:") for k in sent.metadata)

    def test_bcc_is_not_written_as_a_header(self):
        envelope = MailEnvelope(from_email="f@x.co", to=["a@b.co"], bcc=["secret@c.co"], subject="s")
        mime = build_mime_message(envelope)
        assert mime["Bcc"] is None

    def test_inline_attachment_gets_content_id(self):
        envelope = MailEnvelope(from_email="f@x.co", to=["a@b.co"], subject="s")
        from aquilia.mail.envelope import Attachment

        envelope.attachments.append(
            Attachment(
                filename="logo.png",
                content_type="image/png",
                digest="d",
                size=1,
                inline=True,
                content_id="logo",
            )
        )
        envelope.metadata["blob:d"] = b"\x89PNG"
        mime = build_mime_message(envelope)
        cids = [p["Content-ID"] for p in mime.walk() if p["Content-ID"]]
        assert cids == ["<logo>"]

    def test_extract_domain_variants(self):
        assert extract_domain("Asha <a@ex.com>") == "ex.com"
        assert extract_domain("a@ex.com") == "ex.com"
        assert extract_domain("operator") == "localhost"

    def test_extra_headers_are_applied(self):
        envelope = MailEnvelope(from_email="f@x.co", to=["a@b.co"], subject="s")
        mime = build_mime_message(envelope, extra_headers={"X-Custom": "1"})
        assert mime["X-Custom"] == "1"


# ════════════════════════════════════════════════════════════════════
# B2-07 — DKIM + PII redaction are real
# ════════════════════════════════════════════════════════════════════


class TestDkim:
    def test_disabled_dkim_is_a_passthrough(self):
        from aquilia.mail.mime import sign_dkim

        security = SecurityConfig({"dkim_enabled": False})
        assert sign_dkim(b"raw", security) == b"raw"

    def test_enabled_without_domain_raises(self):
        from aquilia.mail.mime import sign_dkim

        security = SecurityConfig({"dkim_enabled": True})
        with pytest.raises(MailConfigFault):
            sign_dkim(b"raw", security)

    def test_enabled_without_key_raises(self, monkeypatch):
        from aquilia.mail.mime import sign_dkim

        pytest.importorskip("dkim")
        monkeypatch.delenv("AQUILIA_DKIM_PRIVATE_KEY", raising=False)
        security = SecurityConfig(
            {
                "dkim_enabled": True,
                "dkim_domain": "example.com",
                "dkim_private_key_path": None,
                "dkim_private_key_env": "AQUILIA_DKIM_PRIVATE_KEY",
            }
        )
        with pytest.raises(MailConfigFault):
            sign_dkim(b"From: a@example.com\r\n\r\nbody", security)

    def test_signature_prepended_when_configured(self, tmp_path):
        pytest.importorskip("dkim")
        crypto = pytest.importorskip("cryptography.hazmat.primitives.asymmetric.rsa")
        from cryptography.hazmat.primitives import serialization

        key = crypto.generate_private_key(public_exponent=65537, key_size=2048)
        pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
        key_path = tmp_path / "dkim.pem"
        key_path.write_bytes(pem)

        from aquilia.mail.mime import sign_dkim

        security = SecurityConfig(
            {
                "dkim_enabled": True,
                "dkim_domain": "example.com",
                "dkim_selector": "aquilia",
                "dkim_private_key_path": str(key_path),
            }
        )
        raw = b"From: a@example.com\r\nTo: b@example.com\r\nSubject: s\r\n\r\nbody\r\n"
        signed = sign_dkim(raw, security)
        assert signed.startswith(b"DKIM-Signature:")
        assert signed.endswith(raw)


class TestDkimWiring:
    """
    Verify the signer is driven correctly without depending on ``dkimpy``.

    A stub module stands in for ``dkim``, so these run everywhere and assert
    what Aquilia controls: key loading precedence, selector/domain encoding,
    header ordering, and failure translation.
    """

    @staticmethod
    def _install_stub(monkeypatch, *, calls: list[dict], fail: bool = False):
        import sys
        import types

        module = types.ModuleType("dkim")

        def _sign(**kwargs):
            calls.append(kwargs)
            if fail:
                raise RuntimeError("stub signer refused")
            return b"DKIM-Signature: v=1; stub\r\n"

        module.sign = _sign
        monkeypatch.setitem(sys.modules, "dkim", module)

    def test_key_loaded_from_env_when_no_path(self, monkeypatch):
        from aquilia.mail.mime import sign_dkim

        calls: list[dict] = []
        self._install_stub(monkeypatch, calls=calls)
        monkeypatch.setenv("TEST_DKIM_KEY", "PEM-BODY")

        security = SecurityConfig(
            {
                "dkim_enabled": True,
                "dkim_domain": "example.com",
                "dkim_selector": "sel",
                "dkim_private_key_path": None,
                "dkim_private_key_env": "TEST_DKIM_KEY",
            }
        )
        out = sign_dkim(b"raw-message", security)

        assert out == b"DKIM-Signature: v=1; stub\r\nraw-message"
        assert calls[0]["privkey"] == b"PEM-BODY"
        assert calls[0]["domain"] == b"example.com"
        assert calls[0]["selector"] == b"sel"
        assert calls[0]["include_headers"][:3] == [b"From", b"To", b"Subject"]

    def test_path_wins_over_env(self, monkeypatch, tmp_path):
        from aquilia.mail.mime import sign_dkim

        calls: list[dict] = []
        self._install_stub(monkeypatch, calls=calls)
        monkeypatch.setenv("TEST_DKIM_KEY", "FROM-ENV")
        key_path = tmp_path / "k.pem"
        key_path.write_bytes(b"FROM-FILE")

        security = SecurityConfig(
            {
                "dkim_enabled": True,
                "dkim_domain": "example.com",
                "dkim_private_key_path": str(key_path),
                "dkim_private_key_env": "TEST_DKIM_KEY",
            }
        )
        sign_dkim(b"raw", security)
        assert calls[0]["privkey"] == b"FROM-FILE"

    def test_unreadable_key_path_raises_config_fault(self, monkeypatch, tmp_path):
        from aquilia.mail.mime import sign_dkim

        self._install_stub(monkeypatch, calls=[])
        security = SecurityConfig(
            {
                "dkim_enabled": True,
                "dkim_domain": "example.com",
                "dkim_private_key_path": str(tmp_path / "missing.pem"),
            }
        )
        with pytest.raises(MailConfigFault):
            sign_dkim(b"raw", security)

    def test_signer_failure_becomes_send_fault(self, monkeypatch):
        from aquilia.mail.mime import sign_dkim

        self._install_stub(monkeypatch, calls=[], fail=True)
        monkeypatch.setenv("TEST_DKIM_KEY", "PEM")
        security = SecurityConfig(
            {
                "dkim_enabled": True,
                "dkim_domain": "example.com",
                "dkim_private_key_env": "TEST_DKIM_KEY",
            }
        )
        with pytest.raises(MailSendFault):
            sign_dkim(b"raw", security)

    def test_message_to_bytes_signs_when_security_given(self, monkeypatch):
        from aquilia.mail.mime import message_to_bytes

        calls: list[dict] = []
        self._install_stub(monkeypatch, calls=calls)
        monkeypatch.setenv("TEST_DKIM_KEY", "PEM")
        security = SecurityConfig(
            {
                "dkim_enabled": True,
                "dkim_domain": "example.com",
                "dkim_private_key_env": "TEST_DKIM_KEY",
            }
        )
        envelope = MailEnvelope(from_email="f@x.co", to=["a@b.co"], subject="s", body_text="b")
        out = message_to_bytes(build_mime_message(envelope), security)
        assert out.startswith(b"DKIM-Signature:")
        assert len(calls) == 1

    def test_message_to_bytes_without_security_does_not_sign(self):
        from aquilia.mail.mime import message_to_bytes

        envelope = MailEnvelope(from_email="f@x.co", to=["a@b.co"], subject="s", body_text="b")
        out = message_to_bytes(build_mime_message(envelope))
        assert not out.startswith(b"DKIM-Signature:")

    def test_ses_raw_send_path_signs(self, monkeypatch):
        calls: list[dict] = []
        self._install_stub(monkeypatch, calls=calls)
        monkeypatch.setenv("TEST_DKIM_KEY", "PEM")
        security = SecurityConfig(
            {
                "dkim_enabled": True,
                "dkim_domain": "example.com",
                "dkim_private_key_env": "TEST_DKIM_KEY",
            }
        )
        provider = SESProvider(name="ses", security=security)
        envelope = MailEnvelope(from_email="f@x.co", to=["a@b.co"], subject="s", body_text="b")
        raw = provider._build_raw_message(envelope)
        assert raw.startswith(b"DKIM-Signature:")


class _FakeSmtpConnection:
    """Records which aiosmtplib call path a send took."""

    def __init__(self) -> None:
        self.sendmail_calls: list[tuple[str, list[str], bytes]] = []
        self.send_message_calls: list[object] = []

    async def sendmail(self, sender, recipients, message):
        self.sendmail_calls.append((sender, list(recipients), message))
        return {}, "250 queued"

    async def send_message(self, message, sender=None, recipients=None):
        self.send_message_calls.append(message)
        return {}, "250 queued"


class TestSmtpDkimPath:
    """
    With DKIM on, SMTP must use ``sendmail`` with pre-signed bytes.

    ``send_message`` re-renders the message object, which would reorder or
    refold headers and invalidate the signature we just computed.
    """

    async def test_dkim_enabled_uses_sendmail_with_signed_bytes(self, monkeypatch):
        TestDkimWiring._install_stub(monkeypatch, calls=[])
        monkeypatch.setenv("TEST_DKIM_KEY", "PEM")
        security = SecurityConfig(
            {
                "dkim_enabled": True,
                "dkim_domain": "example.com",
                "dkim_private_key_env": "TEST_DKIM_KEY",
            }
        )
        provider = SMTPProvider(name="s", security=security)
        conn = _FakeSmtpConnection()
        envelope = MailEnvelope(from_email="f@x.co", to=["a@b.co"], subject="s", body_text="b")

        await provider._transmit(conn, envelope)

        assert conn.send_message_calls == []
        assert len(conn.sendmail_calls) == 1
        sender, recipients, raw = conn.sendmail_calls[0]
        assert sender == "f@x.co"
        assert recipients == ["a@b.co"]
        assert raw.startswith(b"DKIM-Signature:")

    async def test_dkim_disabled_uses_send_message(self):
        provider = SMTPProvider(name="s", security=SecurityConfig({"dkim_enabled": False}))
        conn = _FakeSmtpConnection()
        envelope = MailEnvelope(from_email="f@x.co", to=["a@b.co"], subject="s", body_text="b")

        await provider._transmit(conn, envelope)

        assert conn.sendmail_calls == []
        assert len(conn.send_message_calls) == 1

    async def test_no_security_config_uses_send_message(self):
        provider = SMTPProvider(name="s")
        conn = _FakeSmtpConnection()
        envelope = MailEnvelope(from_email="f@x.co", to=["a@b.co"], subject="s", body_text="b")

        await provider._transmit(conn, envelope)

        assert len(conn.send_message_calls) == 1

    async def test_bcc_recipients_included_in_transport_list(self, monkeypatch):
        TestDkimWiring._install_stub(monkeypatch, calls=[])
        monkeypatch.setenv("TEST_DKIM_KEY", "PEM")
        provider = SMTPProvider(
            name="s",
            security=SecurityConfig(
                {
                    "dkim_enabled": True,
                    "dkim_domain": "example.com",
                    "dkim_private_key_env": "TEST_DKIM_KEY",
                }
            ),
        )
        conn = _FakeSmtpConnection()
        envelope = MailEnvelope(
            from_email="f@x.co",
            to=["a@b.co"],
            bcc=["hidden@c.co"],
            subject="s",
            body_text="b",
        )

        await provider._transmit(conn, envelope)

        _sender, recipients, raw = conn.sendmail_calls[0]
        assert "hidden@c.co" in recipients
        assert b"hidden@c.co" not in raw  # never leaked as a header

    def test_to_dict_reports_configured_rate_limit(self):
        provider = SMTPProvider(name="s", rate_limit_per_min=42)
        assert provider.to_dict()["rate_limit_per_min"] == 42


class TestPiiRedaction:
    def test_local_part_masked_keeping_first_and_last(self):
        assert redact_email("asha.rao@example.com") == "a******o@example.com"

    def test_two_char_local_part(self):
        assert redact_email("bo@x.io") == "b*@x.io"

    def test_single_char_local_part_unchanged(self):
        assert redact_email("a@x.io") == "a@x.io"

    def test_non_address_unchanged(self):
        assert redact_email("not-an-address") == "not-an-address"

    def test_redacts_all_addresses_in_text(self):
        out = redact_pii("failed for asha@x.io and cc bob@y.org")
        assert "asha@x.io" not in out
        assert "bob@y.org" not in out
        assert "x.io" in out and "y.org" in out

    def test_disabled_is_passthrough(self):
        assert redact_pii("asha@x.io", enabled=False) == "asha@x.io"

    def test_empty_input(self):
        assert redact_pii("") == ""

    async def test_service_scrub_respects_config(self):
        on = _service_with(
            _RecordingProvider("p"),
            config=MailConfig(security={"pii_redaction_enabled": True}),
        )
        off = _service_with(
            _RecordingProvider("p"),
            config=MailConfig(security={"pii_redaction_enabled": False}),
        )
        assert "asha@x.io" not in on._scrub("to asha@x.io")
        assert "asha@x.io" in off._scrub("to asha@x.io")


# ════════════════════════════════════════════════════════════════════
# Integration — template message end-to-end
# ════════════════════════════════════════════════════════════════════


class TestTemplateMessageIntegration:
    async def test_template_body_escaped_but_subject_is_not(self, tmp_path):
        template = tmp_path / "welcome.aqt"
        template.write_text("<p>Hi << user.name >></p>", encoding="utf-8")

        p = _RecordingProvider("p")
        svc = _service_with(p)
        msg = TemplateMessage(
            template=str(template),
            context={"user": {"name": "Asha & <b>Co</b>"}},
            subject="Welcome << user.name >>",
            to="a@b.co",
        )
        await svc.send_message(msg)

        sent = p.sent[0]
        assert "&lt;b&gt;" in sent.body_html
        assert "<b>" not in sent.body_html
        # Subject is a plain-text header -- must NOT be HTML-escaped.
        assert sent.subject == "Welcome Asha & <b>Co</b>"

    async def test_txt_template_is_not_escaped(self, tmp_path):
        template = tmp_path / "receipt.txt"
        template.write_text("Total << amount >>", encoding="utf-8")

        from aquilia.mail.template import render_template

        assert render_template(str(template), {"amount": "A & B"}) == "Total A & B"

    def test_missing_template_raises(self):
        from aquilia.mail.template import render_template

        with pytest.raises(MailTemplateFault):
            render_template("definitely-not-here.aqt", {})


# ════════════════════════════════════════════════════════════════════
# Integration — mail retry executed by the task system
# ════════════════════════════════════════════════════════════════════


class TestMailTaskIntegration:
    async def test_queued_retry_is_executed_by_a_worker(self):
        """End-to-end: transient failure → task queue → successful retry."""

        class FlakyProvider(_RecordingProvider):
            async def send(self, envelope: MailEnvelope) -> ProviderResult:
                self.sent.append(envelope)
                if len(self.sent) == 1:
                    return ProviderResult(
                        status=ProviderResultStatus.TRANSIENT_FAILURE,
                        error_message="temporary",
                        retry_after=0.01,
                    )
                return ProviderResult(status=ProviderResultStatus.SUCCESS, provider_message_id="mid")

        provider = FlakyProvider("flaky")
        svc = _service_with(provider)
        manager = TaskManager(num_workers=1)
        await manager.start()
        svc.bind_task_manager(manager)
        set_mail_service(svc)
        try:
            envelope = MailEnvelope(from_email="f@x.co", to=["a@b.co"], subject="s", body_text="b")
            await svc.send_envelope(envelope)

            for _ in range(300):
                if len(provider.sent) >= 2:
                    break
                await asyncio.sleep(0.01)

            assert len(provider.sent) >= 2
            assert envelope.attempts >= 2
        finally:
            set_mail_service(None)
            await manager.stop(timeout=2.0)

    async def test_task_decorator_still_registers_with_cron_schedule(self):
        """Regression guard: the DOW fix must not break @task registration."""

        @task(name="_audit_cron_task", schedule=cron("0 3 * * 1"))
        async def nightly() -> None:
            return None

        from aquilia.tasks.decorators import get_periodic_tasks

        assert "_audit_cron_task" in get_periodic_tasks()
