"""
aquilia.devplatform.logging — Unified, mode-aware logging pipeline for the ADP.

The dev platform has to satisfy two opposing requirements at once:

  * The default terminal experience must stay **clean and stable** — no GET/POST
    spam, no framework/discovery/lifespan chatter scrolling the dashboard.
  * Nothing may be **lost** — every log record and request event must remain
    available for the Inspector console and for post-mortem debugging.

This module resolves that tension with a single :class:`ADPLogRouter` that owns
one :class:`logging.Handler`. Every record is always captured into a bounded,
thread-safe **ring buffer** (the Inspector's source of truth) and is *only*
mirrored to stdout when the active :class:`LogMode` calls for it. Switching
modes never adds or removes handlers — it just flips which sinks a record
reaches — so there is exactly one wiring path and no duplication.

Modes
-----
``DASHBOARD``  Ring buffer only. stdout stays silent so the live dashboard TUI
              can own the screen. (default under ``aq run``)
``INSPECTOR``  Ring buffer only, same as dashboard — the Inspector renders the
              buffer itself; raw stdout writes would corrupt its layout.
``SILENT``     Ring buffer only, no stdout, and WARNING+ suppressed from any
              incidental console fallback. Quietest possible.
``VERBOSE``    Ring buffer + stdout at INFO. Plain streaming logs, no TUI.
``DEBUG``      Ring buffer + stdout at DEBUG. Everything, including framework
              internals.

Thread-safety
-------------
The ring buffer and subscriber list are guarded by a lock. ``emit`` is called
from arbitrary threads (asyncio callbacks, the memory-tracker thread, the
keyboard thread), so all mutation is serialized. Subscriber callbacks are
invoked outside the lock and defensively wrapped — a broken Inspector
subscriber can never wedge the logging path.
"""

from __future__ import annotations

import logging
import os
import sys
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from aquilia.devplatform.core._base import SingletonMixin

# ── Modes ───────────────────────────────────────────────────────────────────


class LogMode(str, Enum):
    """Terminal logging behaviour for the ADP session."""

    DASHBOARD = "dashboard"  # ring only — live TUI owns the screen
    INSPECTOR = "inspector"  # ring only — Inspector renders the buffer
    SILENT = "silent"  # ring only, WARNING+ suppressed from stdout
    VERBOSE = "verbose"  # ring + stdout @ INFO
    DEBUG = "debug"  # ring + stdout @ DEBUG

    @property
    def writes_stdout(self) -> bool:
        """Whether records in this mode are mirrored to stdout."""
        return self in (LogMode.VERBOSE, LogMode.DEBUG)

    @property
    def stdout_level(self) -> int:
        """Minimum level a record must meet to reach stdout in this mode."""
        return logging.DEBUG if self is LogMode.DEBUG else logging.INFO


# ── Structured event ────────────────────────────────────────────────────────

_LEVEL_COLORS: dict[int, str] = {
    logging.DEBUG: "\033[90m",  # gray
    logging.INFO: "\033[36m",  # cyan
    logging.WARNING: "\033[33m",  # yellow
    logging.ERROR: "\033[31m",  # red
    logging.CRITICAL: "\033[1;41;97m",  # bold white on red
}
_RESET = "\033[0m"
_DIM = "\033[2m"
_BOLD = "\033[1m"
_GRAY = "\033[90m"
_GREEN = "\033[32m"
_BRIGHT_GREEN = "\033[92m"
_BRIGHT_WHITE = "\033[97m"
_BRIGHT_CYAN = "\033[96m"
_BRIGHT_YELLOW = "\033[93m"
_BRIGHT_MAGENTA = "\033[95m"
_BRIGHT_RED = "\033[91m"

# Short, fixed-width tag per event kind (Inspector + streaming console share it).
_KIND_TAGS: dict[str, str] = {
    "request": "REQ",
    "reload": "RLD",
    "discovery": "DSC",
    "lifespan": "LIF",
    "websocket": "WS ",
    "task": "JOB",
    "diagnostic": "DIA",
    "middleware": "MW ",
    "log": "LOG",
}

# HTTP method → colour, for rich request lines.
_METHOD_COLORS: dict[str, str] = {
    "GET": _BRIGHT_CYAN,
    "POST": _BRIGHT_GREEN,
    "PUT": _BRIGHT_YELLOW,
    "PATCH": _BRIGHT_YELLOW,
    "DELETE": _BRIGHT_RED,
    "HEAD": _GRAY,
    "OPTIONS": _GRAY,
}


def _status_color(status: int) -> str:
    if status >= 500:
        return _BRIGHT_RED
    if status >= 400:
        return _BRIGHT_YELLOW
    if status >= 300:
        return _BRIGHT_CYAN
    return _BRIGHT_GREEN


def _latency_color(ms: float) -> str:
    if ms >= 1000:
        return _BRIGHT_RED
    if ms >= 300:
        return _BRIGHT_YELLOW
    return _GREEN


@dataclass(slots=True)
class LogEvent:
    """A single captured log record, decoupled from :class:`logging.LogRecord`.

    Stored in the ring buffer and consumed by the Inspector. Kept small and
    already-formatted so rendering never has to touch the live logging system.
    """

    timestamp: float  # wall-clock (time.time())
    level_no: int
    level_name: str
    logger_name: str
    message: str
    # Optional structured category for Inspector grouping (e.g. "request",
    # "reload", "discovery", "lifespan", "websocket", "task", "diagnostic").
    kind: str = "log"
    # Optional structured payload for rich rendering (e.g. request method /
    # path / status / duration_ms), so formatters colour parts without
    # re-parsing the flattened ``message``.
    meta: dict | None = None

    def _render_request_body(self, *, color: bool) -> str:
        """Colour a request event's parts (method, path, status, latency)."""
        m = self.meta or {}
        method = str(m.get("method", "")).upper()
        path = str(m.get("path", ""))
        status = int(m.get("status", 0) or 0)
        dur = float(m.get("duration_ms", 0.0) or 0.0)
        exc = m.get("exception_type")
        if not color:
            core = f"{method} {path} {status} {dur:.1f}ms"
            return core + (f" [{exc}]" if exc else "")
        method_c = f"{_METHOD_COLORS.get(method, _BRIGHT_WHITE)}{_BOLD}{method:<6}{_RESET}"
        path_c = f"{_BRIGHT_WHITE}{path}{_RESET}"
        status_c = f"{_status_color(status)}{_BOLD}{status}{_RESET}"
        dur_c = f"{_latency_color(dur)}{dur:.1f}ms{_RESET}"
        line = f"{method_c} {path_c} {status_c} {dur_c}"
        if exc:
            line += f" {_DIM}{_BRIGHT_RED}[{exc}]{_RESET}"
        return line

    def format_line(self, *, color: bool = True) -> str:
        """Render a rich single-line representation for the console.

        Layout: ``HH:MM:SS  KIND  LEVEL  logger  message``. Request events get
        a colour-coded method/path/status/latency body; every other kind keeps
        its plain message. Widths are fixed so columns align across rows.
        """
        ts = time.strftime("%H:%M:%S", time.localtime(self.timestamp))
        short_logger = self.logger_name.replace("aquilia.", "")
        tag = _KIND_TAGS.get(self.kind, (self.kind[:3].upper() + "   ")[:3])

        if self.kind == "request" and self.meta:
            body = self._render_request_body(color=color)
        else:
            body = self.message

        if not color:
            return f"{ts} {tag} {self.level_name:<8} {short_logger}  {body}"

        c = _LEVEL_COLORS.get(self.level_no, "")
        ts_c = f"{_GRAY}{ts}{_RESET}"
        tag_c = f"{_DIM}{_BRIGHT_WHITE}{tag}{_RESET}"
        level_c = f"{c}{self.level_name:<8}{_RESET}" if c else f"{self.level_name:<8}"
        logger_c = f"{_DIM}{short_logger}{_RESET}"

        # Color the log body based on level
        if self.kind == "request":
            body_c = body
        elif self.level_no >= logging.ERROR:
            body_c = f"{_BRIGHT_RED}{body}{_RESET}"
        elif self.level_no >= logging.WARNING:
            body_c = f"{_BRIGHT_YELLOW}{body}{_RESET}"
        elif self.level_no == logging.DEBUG:
            body_c = f"{_GRAY}{body}{_RESET}"
        else:
            body_c = body

        return f"{ts_c} {tag_c} {level_c} {logger_c}  {body_c}"


# ── Router ──────────────────────────────────────────────────────────────────


class _RouterHandler(logging.Handler):
    """A :class:`logging.Handler` that forwards every record to the router.

    Deliberately does no formatting or I/O of its own — the router decides
    whether/where the record is written. This is the single handler the ADP
    attaches to the logging tree.
    """

    def __init__(self, router: ADPLogRouter) -> None:
        super().__init__(level=logging.DEBUG)
        self._router = router

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._router.emit(record)
        except Exception:  # pragma: no cover — logging must never raise
            self.handleError(record)


class ADPLogRouter(SingletonMixin):
    """Process-wide logging router for the dev platform.

    Owns one :class:`_RouterHandler`, a bounded ring buffer, and a subscriber
    list. Install once via :meth:`install`; flip behaviour at runtime via
    :meth:`set_mode`. Read history via :meth:`events`; stream live via
    :meth:`subscribe`.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._mode: LogMode = LogMode.DASHBOARD
        self._ring: deque[LogEvent] = deque(maxlen=2000)
        self._subscribers: list[Callable[[LogEvent], None]] = []
        self._handler: _RouterHandler | None = None
        self._attached_loggers: list[str] = []
        self._installed = False
        self._color = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None

    # ── Installation ────────────────────────────────────────────────────────

    def install(
        self,
        *,
        mode: LogMode = LogMode.DASHBOARD,
        logger_names: tuple[str, ...] = ("aquilia", ""),
        ring_size: int = 2000,
    ) -> None:
        """Attach the router handler to the given logger tree (idempotent).

        ``logger_names`` defaults to ``("aquilia", "")`` — the framework tree
        plus the root logger, so third-party records (uvicorn, watchfiles, app
        code) are also captured for the Inspector. Existing stdout handlers on
        those loggers are removed so the router becomes the single sink; the
        router re-emits to stdout itself when the mode calls for it.
        """
        with self._lock:
            self._mode = mode
            if self._ring.maxlen != ring_size:
                self._ring = deque(self._ring, maxlen=ring_size)
            if self._handler is None:
                self._handler = _RouterHandler(self)
            for name in logger_names:
                lg = logging.getLogger(name)
                # Strip pre-existing stream handlers so nothing bypasses the
                # router and writes straight to the terminal.
                for h in list(lg.handlers):
                    if isinstance(h, logging.StreamHandler) and not isinstance(h, _RouterHandler):
                        lg.removeHandler(h)
                if self._handler not in lg.handlers:
                    lg.addHandler(self._handler)
                lg.setLevel(logging.DEBUG)
                if name:
                    lg.propagate = False
                if name not in self._attached_loggers:
                    self._attached_loggers.append(name)
            self._installed = True

    def uninstall(self) -> None:
        """Detach the router handler from all loggers it was attached to."""
        with self._lock:
            if self._handler is not None:
                for name in self._attached_loggers:
                    logging.getLogger(name).removeHandler(self._handler)
            self._attached_loggers.clear()
            self._installed = False

    @property
    def installed(self) -> bool:
        return self._installed

    # ── Mode ────────────────────────────────────────────────────────────────

    def set_mode(self, mode: LogMode) -> None:
        """Change routing behaviour. Never adds/removes handlers."""
        with self._lock:
            self._mode = mode

    @property
    def mode(self) -> LogMode:
        with self._lock:
            return self._mode

    # ── Emit path ───────────────────────────────────────────────────────────

    def emit(self, record: logging.LogRecord) -> None:
        """Capture a record into the ring and, when the mode allows, stdout."""
        try:
            message = record.getMessage()
        except Exception:
            message = str(record.msg)
        event = LogEvent(
            timestamp=record.created,
            level_no=record.levelno,
            level_name=record.levelname,
            logger_name=record.name,
            message=message,
            kind=getattr(record, "adp_kind", "log"),
        )
        self.emit_event(event)

    def emit_event(self, event: LogEvent) -> None:
        """Capture a pre-built :class:`LogEvent` (used for structured events)."""
        with self._lock:
            self._ring.append(event)
            mode = self._mode
            subscribers = tuple(self._subscribers)
            color = self._color

        if mode.writes_stdout and event.level_no >= mode.stdout_level:
            try:
                sys.stdout.write(event.format_line(color=color) + "\n")
                sys.stdout.flush()
            except Exception:  # pragma: no cover
                pass

        for sub in subscribers:
            try:
                sub(event)
            except Exception:  # pragma: no cover — a bad subscriber is isolated
                pass

    def log_event(
        self,
        message: str,
        *,
        level: int = logging.INFO,
        kind: str = "log",
        logger_name: str = "aquilia.devplatform",
        meta: dict | None = None,
    ) -> None:
        """Inject a structured event directly (bypasses the logging module).

        Used for request/reload/discovery/websocket events the ADP surfaces to
        the Inspector without wanting a full :class:`logging.Logger` round-trip.
        ``meta`` carries structured fields (e.g. request method/status/latency)
        for rich, colour-coded rendering.
        """
        self.emit_event(
            LogEvent(
                timestamp=time.time(),
                level_no=level,
                level_name=logging.getLevelName(level),
                logger_name=logger_name,
                message=message,
                kind=kind,
                meta=meta,
            )
        )

    # ── Consumption ─────────────────────────────────────────────────────────

    def events(self, *, limit: int | None = None, kind: str | None = None) -> list[LogEvent]:
        """Return buffered events, newest last, optionally filtered by kind."""
        with self._lock:
            items = list(self._ring)
        if kind is not None:
            items = [e for e in items if e.kind == kind]
        if limit is not None:
            items = items[-limit:]
        return items

    def clear(self) -> None:
        with self._lock:
            self._ring.clear()

    def subscribe(self, callback: Callable[[LogEvent], None]) -> Callable[[], None]:
        """Register a live callback; returns an unsubscribe callable."""
        with self._lock:
            self._subscribers.append(callback)

        def _unsub() -> None:
            with self._lock:
                if callback in self._subscribers:
                    self._subscribers.remove(callback)

        return _unsub


def get_router() -> ADPLogRouter:
    """Return the process-wide :class:`ADPLogRouter` singleton."""
    return ADPLogRouter.get_instance()
