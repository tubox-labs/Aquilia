"""
aquilia.devplatform.ui — Terminal UI for the Aquilia Native Development Platform.

A professional, emoji-free, keyboard-driven terminal interface in the spirit of
Bun, Cargo, Turborepo, Docker, Railway, and Vercel's CLIs. Pure stdlib (no
external TUI dependency): ``sys``, ``os``, ``termios``, ``tty``, ``signal``,
``threading``.

Three modes, switchable at runtime without restarting the server:

  * **Startup** (default) — a minimal, stable banner: URL, environment,
    transport, WebSocket mode, reload status, PID, startup duration, workspace.
    Nothing scrolls; runtime logs are suppressed here.
  * **Dashboard** (``D``) — a live full-screen panel (alternate screen buffer,
    ~4 Hz repaint) of CPU, memory, event-loop lag, throughput, error rate,
    active connections/tasks/websockets, reload/discovery status, background
    jobs, and cache statistics.
  * **Inspector** (``I``) — a live observability console rendering the captured
    log/event ring buffer: application logs, request/response/exception traces,
    discovery, reload, diagnostic, middleware, lifespan, background-task, and
    WebSocket events, colour-coded by level.

Keyboard input runs on a background daemon thread in cbreak mode so it never
blocks the asyncio event loop. On a non-TTY (CI, piped output) the UI degrades
to printing the static banner once and doing nothing else.
"""

from __future__ import annotations

import os
import signal
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import replace
from typing import TYPE_CHECKING

from aquilia.devplatform.logging import LogEvent, LogMode, get_router

if TYPE_CHECKING:
    from aquilia.devplatform.config import AquiliaDevelopmentConfig
    from aquilia.devplatform.core.runtime import RuntimeStateStore

# ── ANSI helpers ────────────────────────────────────────────────────────────

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_CYAN = "\033[36m"
_BRIGHT_CYAN = "\033[96m"
_GREEN = "\033[32m"
_BRIGHT_GREEN = "\033[92m"
_YELLOW = "\033[33m"
_BRIGHT_YELLOW = "\033[93m"
_BLUE = "\033[34m"
_BRIGHT_BLUE = "\033[94m"
_MAGENTA = "\033[35m"
_BRIGHT_MAGENTA = "\033[95m"
_WHITE = "\033[37m"
_BRIGHT_WHITE = "\033[97m"
_GRAY = "\033[90m"
_RED = "\033[31m"
_BRIGHT_RED = "\033[91m"

# Alternate-screen / cursor control
_ALT_ENTER = "\033[?1049h"
_ALT_EXIT = "\033[?1049l"
_CURSOR_HIDE = "\033[?25l"
_CURSOR_SHOW = "\033[?25h"
_CLEAR_HOME = "\033[2J\033[H"


def _supports_color() -> bool:
    return sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def _c(text: str, *codes: str) -> str:
    """Apply ANSI colour codes when stdout is a colour-capable TTY."""
    if not _supports_color():
        return text
    return "".join(codes) + text + _RESET


def _w(text: str) -> None:
    """Write to stdout and flush immediately (best-effort)."""
    try:
        sys.stdout.write(text)
        sys.stdout.flush()
    except Exception:
        pass


def _clear() -> None:
    """Clear the terminal screen."""
    if sys.platform == "win32":
        os.system("cls")
    else:
        _w(_CLEAR_HOME)


def _fmt_bytes(n: int) -> str:
    """Human-readable byte size."""
    if n <= 0:
        return "—"
    units = ("B", "KB", "MB", "GB", "TB")
    size = float(n)
    for unit in units:
        if size < 1024.0 or unit == units[-1]:
            return f"{size:.0f}{unit}" if unit == "B" else f"{size:.1f}{unit}"
        size /= 1024.0
    return f"{size:.1f}TB"


def _fmt_duration(seconds: float) -> str:
    """Compact uptime formatting (s / m / h)."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    if seconds < 3600:
        return f"{seconds / 60:.0f}m{seconds % 60:.0f}s"
    return f"{seconds / 3600:.0f}h{(seconds % 3600) / 60:.0f}m"


# ── Modes ──────────────────────────────────────────��────────────────────────

_MODE_STARTUP = "startup"
_MODE_DASHBOARD = "dashboard"
_MODE_INSPECTOR = "inspector"


class ADPTerminalUI:
    """Keyboard-driven, mode-switching terminal UI for the ADP.

    Usage::

        ui = ADPTerminalUI(config, runtime, mode="dev",
                           on_reload=..., on_quit=...)
        ui.render_header()
        ui.start()      # background keyboard + render threads
        # ... server runs ...
        ui.stop()       # restores terminal, exits alt-screen

    All terminal-state mutation (cbreak, alternate screen, cursor visibility)
    is unwound on :meth:`stop`, on process exit (``atexit``), and on any thread
    exit path, so the terminal is never left in a broken state — even across a
    hot-reload ``os.execv``.
    """

    def __init__(
        self,
        config: AquiliaDevelopmentConfig,
        runtime: RuntimeStateStore | None = None,
        mode: str = "dev",
        on_reload: Callable[[], None] | None = None,
        on_quit: Callable[[], None] | None = None,
        *,
        refresh_hz: float = 4.0,
    ) -> None:
        self._config = config
        self._runtime = runtime
        self._mode = mode  # runtime mode label (dev/test) — not the UI mode
        self._on_reload = on_reload
        self._on_quit = on_quit
        self._refresh_interval = 1.0 / max(1.0, refresh_hz)

        self._running = False
        self._kb_thread: threading.Thread | None = None
        self._render_thread: threading.Thread | None = None
        self._ui_mode = _MODE_STARTUP
        self._mode_lock = threading.Lock()
        self._started_at = time.monotonic()

        # Terminal state bookkeeping (POSIX cbreak restore)
        self._termios_fd: int | None = None
        self._termios_saved: object | None = None
        self._in_alt_screen = False
        self._atexit_registered = False

        # Live request/log streamer for the startup view.
        self._unsub_stream: Callable[[], None] | None = None

    # ── Public API ──────────────────────────────────────────────────────────

    def render_header(self) -> None:
        """Print the minimal, stable startup banner once."""
        cfg = self._config
        is_tty = sys.stdout.isatty()
        from pathlib import Path

        startup_ms = (time.monotonic() - self._started_at) * 1000.0

        bind = f"unix:{cfg.uds}" if cfg.uds else (f"fd:{cfg.fd}" if cfg.fd else f"http://{cfg.host}:{cfg.port}")
        workspace = str(Path(os.environ.get("AQUILIA_WORKSPACE", os.getcwd())).resolve())

        # Frame width
        width = 62

        if not is_tty:
            lines = [
                "Aquilia Native Development Platform",
                f"App:          {bind}",
                f"Environment:  {self._mode.upper()}",
                f"Transport:    {cfg.http}",
                f"WebSocket:    {cfg.ws}",
                f"Reload:       {'enabled' if cfg.reload else 'disabled'}",
                f"Process:      {os.getpid()}",
                f"Startup:      {startup_ms:.0f}ms",
                f"Workspace:    {workspace}",
                "",
            ]
            _w("\n".join(lines))
            return

        # TTY beautiful framed card
        def c_frame(text):
            return _c(text, _GRAY)

        def c_title(text):
            return _c(text, _BOLD, _BRIGHT_WHITE)

        def c_label(text):
            return _c(text, _GRAY)

        mode_color = _BRIGHT_YELLOW if self._mode == "dev" else _BRIGHT_GREEN
        reload_color = _BRIGHT_GREEN if cfg.reload else _GRAY
        reload_status = "enabled" if cfg.reload else "disabled"

        fields = [
            ("App", bind, _BRIGHT_CYAN),
            ("Environment", self._mode.upper(), mode_color),
            ("Transport", cfg.http, _BRIGHT_WHITE),
            ("WebSocket", cfg.ws, _BRIGHT_WHITE),
            ("Reload", reload_status, reload_color),
            ("Process", str(os.getpid()), _BRIGHT_WHITE),
            ("Startup", f"{startup_ms:.0f}ms", _BRIGHT_WHITE),
            ("Workspace", workspace, _GRAY),
        ]

        import shutil

        term_width = shutil.get_terminal_size((80, 20)).columns
        target_width = max(term_width, 80)

        box_margin = max(0, (target_width - width) // 2)
        box_indent = " " * box_margin

        # Centered green ASCII art
        ascii_art = [
            r" █████╗  ██████╗ ██╗   ██╗██╗██╗     ██╗ █████╗",
            r"██╔══██╗██╔═══██╗██║   ██║██║██║     ██║██╔══██╗",
            r"███████║██║   ██║██║   ██║██║██║     ██║███████║",
            r"██╔══██║██║▄▄ ██║██║   ██║██║██║     ██║██╔══██║",
            r"██║  ██║╚██████╔╝╚██████╔╝██║███████╗██║██║  ██║",
            r"╚═╝  ╚═╝ ╚══▀▀═╝  ╚═════╝ ╚═╝╚══════╝╚═╝╚═╝  ╚═╝",
        ]

        ascii_margin = max(0, (target_width - 48) // 2)
        ascii_indent = " " * ascii_margin

        ascii_lines = []
        for line in ascii_art:
            ascii_lines.append(ascii_indent + _c(line, _BRIGHT_GREEN) + "\n")

        subtitle_plain = "Native Development Platform"
        subtitle_margin = max(0, (target_width - 27) // 2)
        subtitle_indent = " " * subtitle_margin
        subtitle_line = subtitle_indent + _c(subtitle_plain, _GRAY) + "\n"

        top = box_indent + c_frame("┌" + "─" * (width - 2) + "┐")

        card_lines = ["\n"] + ascii_lines + [subtitle_line, "\n", top + "\n"]

        for label, val, color in fields:
            max_val_len = 40
            if len(val) > max_val_len:
                val = "..." + val[-(max_val_len - 3) :]

            lbl_plain = f"{label:<12}"
            lbl_colored = c_label(lbl_plain)
            val_colored = _c(val, color)
            padding = " " * (width - 4 - len(lbl_plain) - len(val))

            card_lines.append(box_indent + c_frame("│ ") + lbl_colored + val_colored + padding + c_frame(" │\n"))

        bot = box_indent + c_frame("└" + "─" * (width - 2) + "┘")
        card_lines.append(bot + "\n")

        _w("\n" + "".join(card_lines))
        self._render_hint_bar(box_indent + "  ")

    def start(self) -> None:
        """Start the background keyboard listener and live request streamer."""
        if not sys.stdin.isatty():
            return  # non-interactive — static banner only
        self._running = True
        self._register_atexit()
        self._start_stream()
        self._kb_thread = threading.Thread(target=self._keyboard_loop, daemon=True, name="adp-kb")
        self._kb_thread.start()

    def stop(self) -> None:
        """Stop all UI threads and fully restore terminal state."""
        self._running = False
        self._stop_stream()
        self._stop_render_thread()
        self._leave_alt_screen()
        self._restore_termios()

    # ── Live request streamer (startup view) ────────────────────────────────

    def _start_stream(self) -> None:
        """Stream request lines (and warnings/errors) to stdout in startup view.

        The startup banner otherwise leaves stdout silent, so incoming traffic
        is invisible until you open the Inspector. This subscribes to the log
        router and prints events live — but only while the startup view is
        active, so it never fights the alternate-screen dashboard/inspector.
        """
        if self._unsub_stream is not None:
            return

        def _on_event(ev: LogEvent) -> None:
            if self.ui_mode != _MODE_STARTUP:
                return  # a live full-screen mode owns the terminal
            # Requests always; other logs only at WARNING+ to keep it clean.
            if ev.kind != "request" and ev.level_no < 30:
                return
            _w(ev.format_line(color=_supports_color()) + "\n")

        self._unsub_stream = get_router().subscribe(_on_event)

    def _stop_stream(self) -> None:
        if self._unsub_stream is not None:
            try:
                self._unsub_stream()
            finally:
                self._unsub_stream = None

    # ── Hint bar ──────────────────────────────────────────────────────────

    def _render_hint_bar(self, margin_spaces: str = "  ") -> None:
        hints = [
            ("D", "dashboard"),
            ("I", "inspector"),
            ("R", "reload"),
            ("C", "clear"),
            ("H", "help"),
            ("Q", "quit"),
        ]
        parts = []
        for k, v in hints:
            key_str = f"{_c('[', _GRAY)}{_c(k, _BOLD, _BRIGHT_WHITE)}{_c(']', _GRAY)}"
            parts.append(f"{key_str} {_c(v, _GRAY)}")
        _w(margin_spaces + "  ".join(parts) + "\n\n")

    # ── Keyboard loop ─────────────────────────────────────────────────────

    def _keyboard_loop(self) -> None:
        """Read single keypresses in cbreak mode and dispatch actions."""
        try:
            import termios
            import tty

            fd = sys.stdin.fileno()
            self._termios_fd = fd
            self._termios_saved = termios.tcgetattr(fd)
            try:
                tty.setcbreak(fd)
                while self._running:
                    try:
                        ch = sys.stdin.read(1)
                    except OSError:
                        break
                    if not ch:
                        break
                    self._handle_key(ch.lower())
            finally:
                self._restore_termios()
        except Exception:
            # termios unavailable (Windows / non-POSIX) — degrade silently.
            pass

    def _handle_key(self, ch: str) -> None:
        if ch == "q":
            self._quit()
        elif ch == "r":
            self._trigger_reload()
        elif ch == "c":
            self._to_startup(clear=True)
        elif ch == "d":
            self._enter_mode(_MODE_DASHBOARD)
        elif ch == "i":
            self._enter_mode(_MODE_INSPECTOR)
        elif ch == "h":
            self._show_help()
        elif ch in ("\x1b", "\n", "\r"):
            # Esc / Enter leaves a live mode back to the clean startup view.
            if self.ui_mode != _MODE_STARTUP:
                self._to_startup(clear=True)

    # ── Actions ───────────────────────────────────────────────────────────

    @property
    def ui_mode(self) -> str:
        with self._mode_lock:
            return self._ui_mode

    def _set_ui_mode(self, mode: str) -> None:
        with self._mode_lock:
            self._ui_mode = mode

    def _quit(self) -> None:
        self.stop()
        _w("\n")
        if self._on_quit:
            self._on_quit()
        else:
            os.kill(os.getpid(), signal.SIGTERM)

    def _trigger_reload(self) -> None:
        get_router().log_event("manual reload requested", kind="reload")
        if self._on_reload:
            try:
                self._on_reload()
            except Exception as exc:  # pragma: no cover
                get_router().log_event(f"reload trigger failed: {exc}", kind="reload")

    def _to_startup(self, *, clear: bool = False) -> None:
        """Return to the minimal startup view, tearing down any live mode."""
        self._stop_render_thread()
        self._leave_alt_screen()
        get_router().set_mode(LogMode.DASHBOARD)  # suppress stdout log noise
        self._set_ui_mode(_MODE_STARTUP)
        if clear:
            _clear()
        self.render_header()

    def _enter_mode(self, mode: str) -> None:
        """Switch into a live full-screen mode (dashboard or inspector)."""
        if not sys.stdout.isatty():
            return
        if self.ui_mode == mode:
            return
        self._set_ui_mode(mode)
        # Inspector needs the router to stay ring-only (it renders the buffer);
        # dashboard likewise wants stdout silent so the frame isn't corrupted.
        get_router().set_mode(LogMode.INSPECTOR if mode == _MODE_INSPECTOR else LogMode.DASHBOARD)
        self._enter_alt_screen()
        self._start_render_thread()

    # ── Render thread (live modes) ─────────────────────────────────────────

    def _start_render_thread(self) -> None:
        if self._render_thread and self._render_thread.is_alive():
            return
        self._render_thread = threading.Thread(target=self._render_loop, daemon=True, name="adp-render")
        self._render_thread.start()

    def _stop_render_thread(self) -> None:
        t = self._render_thread
        self._render_thread = None
        if t and t.is_alive() and t is not threading.current_thread():
            t.join(timeout=self._refresh_interval * 3)

    def _render_loop(self) -> None:
        while self._running:
            mode = self.ui_mode
            if mode == _MODE_DASHBOARD:
                frame = self._build_dashboard_frame()
            elif mode == _MODE_INSPECTOR:
                frame = self._build_inspector_frame()
            else:
                break  # back to startup — render thread exits
            _w(_CLEAR_HOME + frame)
            time.sleep(self._refresh_interval)

    # ── Dashboard ─────────────────────────────────────────────────────────

    def _build_dashboard_frame(self) -> str:
        cfg = self._config
        lines: list[str] = []
        title = "Aquilia  ·  Dashboard"
        subtitle = f"{self._mode}  ·  http://{cfg.host}:{cfg.port}"
        lines.append(f"{_c(title, _BOLD, _BRIGHT_WHITE)}   {_c(subtitle, _GRAY)}")
        lines.append(_c("─" * 60, _GRAY))

        if self._runtime is None:
            lines.append(_c("No runtime attached — metrics unavailable.", _YELLOW))
            lines.append("")
            lines.append(_c("D dashboard   I inspector   Esc back   Q quit", _GRAY))
            return "\n".join(lines) + "\n"

        s = self._runtime.snapshot()

        # Three columns per row. Pad on *visible* width (label + value), then
        # colour — padding a pre-coloured string counts ANSI escape bytes and
        # makes cells collide (the "8.9%Memory" bug).
        _LABEL_W = 13
        _CELL_W = 26

        def cell(label: str, value: str, color: str = _BRIGHT_WHITE) -> str:
            label_field = f"{label:<{_LABEL_W}}"
            visible = len(label_field) + len(value)
            pad = " " * max(2, _CELL_W - visible)
            return f"{_c(label_field, _GRAY)}{_c(value, color)}{pad}"

        def row(*cells: str) -> str:
            # Right-trim trailing pad on the last cell so the line ends cleanly.
            return "".join(cells).rstrip()

        cpu_color = _BRIGHT_GREEN if s.cpu_percent < 60 else (_BRIGHT_YELLOW if s.cpu_percent < 85 else _BRIGHT_RED)
        lag_color = (
            _BRIGHT_GREEN if s.event_loop_lag_ms < 5 else (_BRIGHT_YELLOW if s.event_loop_lag_ms < 50 else _BRIGHT_RED)
        )
        lines.append(
            row(
                cell("CPU", f"{s.cpu_percent:.1f}%", cpu_color),
                cell("Memory", _fmt_bytes(s.rss_bytes)),
                cell("Loop lag", f"{s.event_loop_lag_ms:.2f}ms", lag_color),
            )
        )
        err_color = _BRIGHT_RED if s.total_errors else _BRIGHT_GREEN
        lines.append(
            row(
                cell("Requests", str(s.total_requests)),
                cell("RPS (1s)", f"{s.rps_1s:.1f}", _BRIGHT_YELLOW),
                cell("Avg latency", f"{s.avg_latency_ms:.2f}ms", _BRIGHT_MAGENTA),
            )
        )
        lines.append(
            row(
                cell("Errors", str(s.total_errors), err_color),
                cell("Error rate", f"{s.error_rate * 100:.1f}%", err_color),
                cell("Slow reqs", str(s.slow_requests), _BRIGHT_YELLOW if s.slow_requests else _GRAY),
            )
        )
        lines.append(
            row(
                cell("Connections", str(s.active_connections), _BRIGHT_CYAN),
                cell("WebSockets", str(s.active_websockets), _BRIGHT_CYAN),
                cell("Tasks", str(s.active_tasks), _BRIGHT_CYAN),
            )
        )
        lines.append(
            row(
                cell("Uptime", _fmt_duration(s.uptime_s)),
                cell("PID", str(s.worker_pid)),
                cell("Bg jobs", str(s.background_jobs)),
            )
        )
        lines.append(
            row(
                cell("Cache hits", str(s.cache_hits), _BRIGHT_GREEN),
                cell("Cache miss", str(s.cache_misses), _GRAY),
                cell("DB pool", f"{s.db_pool_active}/{s.db_pool_limit}"),
            )
        )
        lines.append(_c("─" * 60, _GRAY))
        reload_txt = _c("on", _BRIGHT_GREEN) if cfg.reload else _c("off", _GRAY)
        lines.append(
            f"{_c('Reload', _GRAY)} {reload_txt}     "
            f"{_c('Transport', _GRAY)} {_c(cfg.http, _BRIGHT_WHITE)}     "
            f"{_c('WS', _GRAY)} {_c(cfg.ws, _BRIGHT_WHITE)}"
        )
        lines.append("")
        lines.append(_c("D dashboard   I inspector   R reload   Esc back   Q quit", _GRAY))
        return "\n".join(lines) + "\n"

    # ── Inspector ─────────────────────────────────────────────────────────

    def _terminal_rows(self) -> int:
        try:
            return max(10, os.get_terminal_size().lines)
        except Exception:
            return 30

    def _build_inspector_frame(self) -> str:
        rows = self._terminal_rows()
        body_rows = max(5, rows - 5)
        events = get_router().events(limit=body_rows)
        total = len(get_router().events())

        lines: list[str] = []
        lines.append(f"{_c('Aquilia  ·  Inspector', _BOLD, _BRIGHT_WHITE)}   {_c(f'{total} events buffered', _GRAY)}")
        lines.append(_c("─" * 72, _GRAY))

        if not events:
            lines.append(_c("No events captured yet. Traffic and framework events appear here.", _GRAY))
        else:
            for ev in events:
                lines.append(self._format_inspector_line(ev))

        while len(lines) < body_rows + 2:
            lines.append("")
        lines.append(_c("─" * 72, _GRAY))
        lines.append(_c("I inspector   D dashboard   C clear view   Esc back   Q quit", _GRAY))
        return "\n".join(lines) + "\n"

    def _format_inspector_line(self, ev: LogEvent) -> str:
        """Render one buffered event, reusing the shared rich formatter.

        Delegates to :meth:`LogEvent.format_line` so the Inspector panel and
        the streaming console stay pixel-identical (same KIND column, same
        colour-coded request method/status/latency). Only long non-request
        messages are truncated to keep the panel width stable.
        """
        color = _supports_color()
        if ev.kind != "request" and len(ev.message) > 120:
            ev = replace(ev, message=ev.message[:119] + "…")
        return ev.format_line(color=color)

    # ── Help ──────────────────────────────────────────────────────────────

    def _show_help(self) -> None:
        if self.ui_mode != _MODE_STARTUP:
            self._to_startup(clear=True)
        _w("\n")
        _w(f"  {_c('Keyboard Shortcuts', _BOLD, _BRIGHT_WHITE)}\n")
        shortcuts = [
            ("D", "Live dashboard (CPU, memory, throughput, health)"),
            ("I", "Inspector console (logs, traces, events)"),
            ("R", "Trigger a hot-reload"),
            ("C", "Clear and return to the startup view"),
            ("Esc", "Leave a live mode, back to startup"),
            ("H", "Show this help"),
            ("Q", "Gracefully shut down the server"),
        ]
        for key, desc in shortcuts:
            _w(f"  {_c(key, _BOLD, _BRIGHT_WHITE):<5} {_c(desc, _GRAY)}\n")
        _w("\n")

    # ── Terminal state management ──────────────────────────────────────────

    def _register_atexit(self) -> None:
        if self._atexit_registered:
            return
        import atexit

        atexit.register(self._emergency_restore)
        self._atexit_registered = True

    def _emergency_restore(self) -> None:
        """Unconditional terminal restore (registered with atexit)."""
        self._leave_alt_screen()
        self._restore_termios()

    def _enter_alt_screen(self) -> None:
        if self._in_alt_screen or not sys.stdout.isatty():
            return
        _w(_ALT_ENTER + _CURSOR_HIDE + _CLEAR_HOME)
        self._in_alt_screen = True

    def _leave_alt_screen(self) -> None:
        if not self._in_alt_screen:
            return
        _w(_CURSOR_SHOW + _ALT_EXIT)
        self._in_alt_screen = False

    def _restore_termios(self) -> None:
        fd = self._termios_fd
        saved = self._termios_saved
        if fd is None or saved is None:
            return
        try:
            import termios

            termios.tcsetattr(fd, termios.TCSADRAIN, saved)
        except Exception:
            pass
