"""
Aquilia CLI -- Interactive prompt toolkit.

Beautiful interactive prompts built on Click.
Provides select menus, confirm toggles, multi-select, and styled
text input -- all with colour-coded feedback.

Arrow-key navigation is handled via raw terminal mode:
  - Unix/macOS: termios + tty
  - Windows:    msvcrt (built-in, no extra dependencies)
"""

from __future__ import annotations

import os
import sys
from typing import Callable, List, Optional, Sequence, Tuple

import platform

import click

from .colors import (
    _CHECK, _CROSS, _ARROW, _L_H,
)

_IS_WINDOWS: bool = platform.system() == "Windows"

# ═══════════════════════════════════════════════════════════════════════════
# Glyphs & colour helpers
# ═══════════════════════════════════════════════════════════════════════════

_RADIO_ON  = "●"
_RADIO_OFF = "○"
_CHECK_ON  = "◼"
_CHECK_OFF = "◻"


def _c(text: str, fg: str = "cyan", bold: bool = False, dim_: bool = False) -> str:
    return click.style(text, fg=fg, bold=bold, dim=dim_)


def _write(text: str) -> None:
    sys.stdout.write(text)
    sys.stdout.flush()


# ANSI helpers
_CLEAR_LINE  = "\033[2K"
_HIDE_CURSOR = "\033[?25l"
_SHOW_CURSOR = "\033[?25h"


def _erase_lines(n: int) -> None:
    """Erase n lines above current cursor position."""
    for _ in range(n):
        _write(f"\033[1A\033[2K")


# ═══════════════════════════════════════════════════════════════════════════
# Raw-mode key reading
# ═══════════════════════════════════════════════════════════════════════════

def _is_tty() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


# Cached fd for stdin so we don't keep calling fileno()
_STDIN_FD: int = -1


def _stdin_fd() -> int:
    global _STDIN_FD
    if _STDIN_FD < 0:
        _STDIN_FD = sys.stdin.fileno()
    return _STDIN_FD


def _drain_stdin() -> None:
    """
    Discard any bytes already sitting in the OS stdin buffer.

    This is critical between a cooked-mode readline() and a raw-mode
    os.read() loop: without it, bytes typed ahead (or leftover echo
    from arrow keys pressed during the previous prompt) are fed into
    the raw reader and misinterpreted.
    """
    if _IS_WINDOWS:
        import msvcrt
        try:
            while msvcrt.kbhit():
                msvcrt.getwch()
        except Exception:
            pass
    else:
        import termios
        try:
            termios.tcflush(_stdin_fd(), termios.TCIFLUSH)
        except Exception:
            pass


def _read_key() -> str:
    """
    Read a single keypress in raw mode.

    On Windows uses msvcrt.getwch() which is always available.
    On Unix uses termios/tty via the OS file descriptor.

    Returns one of:
      'up', 'down', 'enter', 'space', 'tab', 'shift_tab', 'esc',
      or the literal character.
    """
    if _IS_WINDOWS:
        return _read_key_windows()
    return _read_key_unix()


def _read_key_windows() -> str:
    """Windows key reader using msvcrt (built-in, no install needed)."""
    import msvcrt

    ch = msvcrt.getwch()
    if ch in ("\r", "\n"):
        return "enter"
    if ch == " ":
        return "space"
    if ch == "\t":
        return "tab"
    if ch == "\x03":                            # Ctrl-C
        raise KeyboardInterrupt
    if ch == "\x04":                            # Ctrl-D
        raise EOFError
    if ch == "\x1b":                            # ESC (standalone)
        return "esc"
    if ch in ("\x00", "\xe0"):                  # Special / extended key prefix
        ch2 = msvcrt.getwch()
        if ch2 == "H":                          # Up arrow
            return "up"
        if ch2 == "P":                          # Down arrow
            return "down"
        if ch2 == "\x0f":                       # Shift+Tab (Back-Tab)
            return "shift_tab"
        return "esc"
    return ch


def _read_key_unix() -> str:
    """Unix key reader using termios + tty via OS file descriptor."""
    import termios
    import tty

    fd  = _stdin_fd()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = os.read(fd, 1)
        if ch == b"\x1b":                       # ESC / arrow sequence
            # Set a short read timeout so we don't hang if ESC is pressed alone
            import select as _sel
            ready, _, _ = _sel.select([fd], [], [], 0.1)
            if not ready:
                return "esc"
            ch2 = os.read(fd, 1)
            if ch2 == b"[":
                ready2, _, _ = _sel.select([fd], [], [], 0.1)
                if not ready2:
                    return "esc"
                ch3 = os.read(fd, 1)
                if ch3 == b"A":
                    return "up"
                if ch3 == b"B":
                    return "down"
                if ch3 == b"Z":
                    return "shift_tab"
                # Drain any remaining bytes of unknown sequence
                while True:
                    r, _, _ = _sel.select([fd], [], [], 0.05)
                    if not r:
                        break
                    os.read(fd, 16)
                return "esc"
            return "esc"
        if ch in (b"\r", b"\n"):
            return "enter"
        if ch == b" ":
            return "space"
        if ch == b"\t":
            return "tab"
        if ch == b"\x03":                       # Ctrl-C
            raise KeyboardInterrupt
        if ch == b"\x04":                       # Ctrl-D
            raise EOFError
        return ch.decode("utf-8", errors="replace")
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _read_line_fd() -> str:
    """
    Read one line directly from stdin in canonical (cooked) mode.

    On Windows: reads character-by-character via msvcrt.getwch() with
    echo, handling backspace manually (Windows has no terminal line
    discipline exposed via a raw fd).

    On Unix: bypasses Python's TextIOWrapper buffer via the OS fd so
    there are no stale bytes left in a layer that os.read() can't see.
    The terminal's line discipline still handles editing (backspace etc.)
    because we are NOT in raw mode here.
    """
    if _IS_WINDOWS:
        return _read_line_fd_windows()
    return _read_line_fd_unix()


def _read_line_fd_windows() -> str:
    """Windows line reader using msvcrt character-by-character."""
    import msvcrt

    buf = ""
    while True:
        ch = msvcrt.getwch()
        if ch in ("\r", "\n"):
            msvcrt.putch(b"\n")             # echo newline
            break
        if ch == "\x03":                    # Ctrl-C
            raise KeyboardInterrupt
        if ch == "\x04":                    # Ctrl-D
            if not buf:
                raise EOFError
            break
        if ch in ("\x08", "\x7f"):          # Backspace / DEL
            if buf:
                buf = buf[:-1]
                msvcrt.putch(b"\x08")       # move cursor back
                msvcrt.putch(b" ")          # overwrite with space
                msvcrt.putch(b"\x08")       # move cursor back again
            continue
        if ch in ("\x00", "\xe0"):          # Extended key prefix — skip next byte
            msvcrt.getwch()
            continue
        msvcrt.putwch(ch)                   # echo the character
        buf += ch
    return buf


def _read_line_fd_unix() -> str:
    """Unix line reader via OS fd in canonical (cooked) mode."""
    import termios

    fd  = _stdin_fd()
    old = termios.tcgetattr(fd)
    # Ensure canonical mode + echo are ON (reset any lingering raw state)
    new = termios.tcgetattr(fd)
    new[3] |= termios.ICANON | termios.ECHO   # lflags
    termios.tcsetattr(fd, termios.TCSANOW, new)
    try:
        buf = b""
        while True:
            ch = os.read(fd, 1)
            if ch in (b"\r", b"\n"):
                break
            if ch == b"\x03":
                raise KeyboardInterrupt
            if ch == b"\x04":
                if not buf:
                    raise EOFError
                break
            buf += ch
        return buf.decode("utf-8", errors="replace")
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _read_line() -> str:
    """Read a full line -- uses fd-based reader on TTY, fallback on pipes."""
    if _is_tty():
        try:
            return _read_line_fd()
        except Exception:
            pass
    try:
        return sys.stdin.readline().rstrip("\n")
    except (EOFError, KeyboardInterrupt):
        return ""


# ═══════════════════════════════════════════════════════════════════════════
# Flow banners
# ═══════════════════════════════════════════════════════════════════════════

def flow_header(title: str, subtitle: str = "", *, fg: str = "cyan") -> None:
    """Print a minimal flow header."""
    click.echo()
    click.echo(f"  {_c(title, fg=fg, bold=True)}")
    if subtitle:
        click.echo(f"  {_c(subtitle, dim_=True)}")
    click.echo()


def flow_done(message: str = "Done.", *, fg: str = "green") -> None:
    click.echo()
    click.echo(f"  {_c(_CHECK, fg=fg)} {_c(message, fg=fg, bold=True)}")
    click.echo()


# ═══════════════════════════════════════════════════════════════════════════
# Render helpers shared by select / multi_select
# ═══════════════════════════════════════════════════════════════════════════

def _render_select_rows(
    choices: Sequence[Tuple[str, str]],
    current: int,
) -> None:
    for i, (value, desc) in enumerate(choices):
        active  = i == current
        pointer = _c("", fg="cyan") if active else "  "
        marker  = _c(_RADIO_ON, fg="cyan") if active else _c(_RADIO_OFF, dim_=True)
        val     = _c(value, fg="cyan", bold=True) if active else _c(value, fg="white")
        d       = f"  {_c('─', dim_=True)} {_c(desc, dim_=True)}" if desc else ""
        _write(f"  {pointer} {marker} {val}{d}\n")


def _render_multi_rows(
    choices: Sequence[Tuple[str, str, bool]],
    current: int,
    selected: List[bool],
) -> None:
    for i, (value, desc, _) in enumerate(choices):
        active  = i == current
        on      = selected[i]
        pointer = _c("", fg="cyan") if active else "  "
        marker  = _c(_CHECK_ON, fg="green") if on else _c(_CHECK_OFF, dim_=True)
        val     = (
            _c(value, fg="cyan",  bold=True) if active else
            _c(value, fg="white", bold=True) if on     else
            _c(value, fg="white")
        )
        d = f"  {_c('─', dim_=True)} {_c(desc, dim_=True)}" if desc else ""
        _write(f"  {pointer} {marker} {val}{d}\n")


# ═══════════════════════════════════════════════════════════════════════════
# Text input
# ═══════════════════════════════════════════════════════════════════════════

def ask(
    label: str,
    *,
    default: str = "",
    required: bool = False,
    validator: Optional[Callable[[str], Optional[str]]] = None,
    hint: str = "",
) -> str:
    """Styled text input prompt with optional validation."""
    while True:
        suffix   = f" ({_c(default, fg='white', dim_=True)})" if default else ""
        hint_str = f"  {_c(hint, dim_=True)}" if hint else ""
        _write(
            f"  {_c('◆', fg='cyan')} {_c(label, fg='white', bold=True)}"
            f"{suffix}{hint_str} {_c('…', dim_=True)} "
        )

        value = _read_line()

        if not value and default:
            value = default

        if required and not value.strip():
            _write(f"    {_c(_CROSS, fg='red')} {_c('This field is required', fg='red')}\n")
            continue

        if validator:
            err = validator(value)
            if err:
                _write(f"    {_c(_CROSS, fg='red')} {_c(err, fg='red')}\n")
                continue

        return value


def ask_password(
    label: str,
    *,
    confirm: bool = True,
    min_length: int = 4,
) -> str:
    """Styled hidden password input with optional confirmation."""
    while True:
        prompt_text = (
            f"  {_c('◆', fg='cyan')} {_c(label, fg='white', bold=True)} "
            f"{_c('…', dim_=True)} "
        )
        value = click.prompt(
            "", prompt_suffix="", hide_input=True, default="", show_default=False
        )
        _write(f"\033[1A\033[2K{prompt_text}{_c('*' * len(value), dim_=True)}\n")

        if len(value) < min_length:
            _write(
                f"    {_c(_CROSS, fg='red')} "
                f"{_c(f'Must be at least {min_length} characters', fg='red')}\n"
            )
            continue

        if confirm:
            confirm_text = (
                f"  {_c('◆', fg='cyan')} {_c('Confirm password', fg='white', bold=True)} "
                f"{_c('…', dim_=True)} "
            )
            confirm_val = click.prompt(
                "", prompt_suffix="", hide_input=True, default="", show_default=False
            )
            _write(
                f"\033[1A\033[2K{confirm_text}"
                f"{_c('*' * len(confirm_val), dim_=True)}\n"
            )
            if value != confirm_val:
                _write(
                    f"    {_c(_CROSS, fg='red')} "
                    f"{_c('Passwords do not match', fg='red')}\n"
                )
                continue

        return value


# ═══════════════════════════════════════════════════════════════════════════
# Select -- single-choice, ↑↓ navigation
# ═══════════════════════════════════════════════════════════════════════════

def select(
    label: str,
    choices: Sequence[Tuple[str, str]],
    *,
    default: int = 0,
) -> str:
    """
    Single-choice select menu with ↑↓ arrow-key navigation.

    Falls back to numbered input when stdin is not a tty (pipes/CI).

    Args:
        label:   Prompt label
        choices: List of (value, description) tuples
        default: Initially highlighted index (0-based)

    Returns:
        Selected value string
    """
    n       = len(choices)
    current = max(0, min(default, n - 1))

    # ── Non-TTY fallback ────────────────────────────────────────────
    if not _is_tty():
        _write(f"  {_c('◆', fg='cyan')} {_c(label, fg='white', bold=True)}\n")
        for i, (value, desc) in enumerate(choices):
            mark = _c(f"{i + 1}.", dim_=True)
            v    = _c(value, fg="cyan" if i == default else "white")
            d    = f"  {_c('─', dim_=True)} {_c(desc, dim_=True)}" if desc else ""
            _write(f"    {mark} {v}{d}\n")
        while True:
            _write(f"  {_c(_ARROW, fg='cyan')} ")
            raw = _read_line().strip()
            if not raw:
                return choices[default][0]
            try:
                idx = int(raw) - 1
                if 0 <= idx < n:
                    return choices[idx][0]
            except ValueError:
                for value, _ in choices:
                    if raw.lower() == value.lower():
                        return value
            _write(f"    {_c(_CROSS, fg='red')} {_c(f'Enter 1–{n}', fg='red')}\n")

    # ── Interactive TTY mode ────────────────────────────────────────
    hint   = _c("↑↓ navigate  Enter confirm", dim_=True)
    header = f"  {_c('◆', fg='cyan')} {_c(label, fg='white', bold=True)}  {hint}\n"

    _drain_stdin()   # flush buffered bytes from any preceding cooked prompt
    _write(_HIDE_CURSOR)
    try:
        _write(header)
        _render_select_rows(choices, current)

        while True:
            key = _read_key()

            if key in ("up", "shift_tab"):
                current = (current - 1) % n
            elif key in ("down", "tab"):
                current = (current + 1) % n
            elif key == "enter":
                _erase_lines(n)
                _write(
                    f"  {_c('◆', fg='cyan')} {_c(label, fg='white', bold=True)}"
                    f"  {_c(choices[current][0], fg='cyan', bold=True)}\n"
                )
                return choices[current][0]
            else:
                continue

            _erase_lines(n)
            _render_select_rows(choices, current)

    except (KeyboardInterrupt, EOFError):
        _write("\n")
        raise
    finally:
        _write(_SHOW_CURSOR)


# ═══════════════════════════════════════════════════════════════════════════
# Multi-select -- toggle, ↑↓ + Space
# ═══════════════════════════════════════════════════════════════════════════

def multi_select(
    label: str,
    choices: Sequence[Tuple[str, str, bool]],
) -> List[str]:
    """
    Multi-choice toggle menu with ↑↓ navigation and Space to toggle.

    Falls back to comma-separated number input when stdin is not a tty.

    Args:
        label:   Prompt label
        choices: List of (value, description, default_on) tuples

    Returns:
        List of selected value strings
    """
    n        = len(choices)
    selected = [on for _, _, on in choices]
    current  = 0

    # ── Non-TTY fallback ────────────────────────────────────────────
    if not _is_tty():
        _write(
            f"  {_c('◆', fg='cyan')} {_c(label, fg='white', bold=True)}"
            f"  {_c('(comma-separated numbers, Enter for defaults)', dim_=True)}\n"
        )
        for i, (value, desc, on) in enumerate(choices):
            mark = _c(_CHECK_ON if on else _CHECK_OFF,
                      fg="green" if on else "white", dim_=not on)
            num  = _c(f"{i + 1}.", dim_=True)
            v    = _c(value, fg="white", bold=on)
            d    = f"  {_c('─', dim_=True)} {_c(desc, dim_=True)}" if desc else ""
            _write(f"    {mark} {num} {v}{d}\n")
        _write(f"  {_c(_ARROW, fg='cyan')} ")
        raw = _read_line().strip()
        if not raw:
            return [v for v, _, on in choices if on]
        result: List[str] = []
        for part in raw.replace(" ", "").split(","):
            try:
                idx = int(part) - 1
                if 0 <= idx < n:
                    val = choices[idx][0]
                    if val not in result:
                        result.append(val)
            except ValueError:
                continue
        return result

    # ── Interactive TTY mode ────────────────────────────────────────
    hint   = _c("↑↓ navigate  Space toggle  Enter confirm", dim_=True)
    header = f"  {_c('◆', fg='cyan')} {_c(label, fg='white', bold=True)}  {hint}\n"

    _drain_stdin()   # flush buffered bytes from any preceding cooked prompt
    _write(_HIDE_CURSOR)
    try:
        _write(header)
        _render_multi_rows(choices, current, selected)

        while True:
            key = _read_key()

            if key in ("up", "shift_tab"):
                current = (current - 1) % n
            elif key in ("down", "tab"):
                current = (current + 1) % n
            elif key == "space":
                selected[current] = not selected[current]
            elif key == "enter":
                result_vals = [choices[i][0] for i in range(n) if selected[i]]
                summary = (
                    ", ".join(result_vals) if result_vals
                    else _c("none", dim_=True)
                )
                _erase_lines(n)
                _write(
                    f"  {_c('◆', fg='cyan')} {_c(label, fg='white', bold=True)}"
                    f"  {_c(summary, fg='cyan')}\n"
                )
                return result_vals
            else:
                continue

            _erase_lines(n)
            _render_multi_rows(choices, current, selected)

    except (KeyboardInterrupt, EOFError):
        _write("\n")
        raise
    finally:
        _write(_SHOW_CURSOR)


# ═══════════════════════════════════════════════════════════════════════════
# Confirm (yes/no)
# ═══════════════════════════════════════════════════════════════════════════

def confirm(
    label: str,
    *,
    default: bool = True,
) -> bool:
    """Styled yes/no prompt."""
    hint = "Y/n" if default else "y/N"
    _write(
        f"  {_c('◆', fg='cyan')} {_c(label, fg='white', bold=True)} "
        f"{_c(f'({hint})', dim_=True)} {_c('…', dim_=True)} "
    )
    raw = _read_line().strip().lower()
    if not raw:
        return default
    return raw in ("y", "yes", "1", "true")


# ═══════════════════════════════════════════════════════════════════════════
# Summary / recap table
# ═══════════════════════════════════════════════════════════════════════════

def recap(items: Sequence[Tuple[str, str]], *, title: str = "Summary") -> None:
    """Print a labelled summary of selected options."""
    click.echo()
    click.echo(
        f"  {_c(_L_H * 2, dim_=True)} "
        f"{_c(title, fg='cyan', bold=True)} "
        f"{_c(_L_H * 36, dim_=True)}"
    )
    for key, value in items:
        k       = _c(f"  {key}:", fg="white")
        v       = _c(value, fg="cyan")
        padding = " " * max(1, 20 - len(key))
        click.echo(f"  {k}{padding}{v}")
    click.echo()
