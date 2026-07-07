"""
Aquilia Model Signals -- pre/post save, delete, init hooks.

Provides a lightweight signal/event system for model lifecycle events,
with support for weak references, priority ordering, sender filtering,
and temporary connections.

Usage:
    from aquilia.models.signals import pre_save, post_save, pre_delete, post_delete

    @pre_save.connect
    async def hash_password(sender, instance, **kwargs):
        if sender.__name__ == "User" and instance.password_changed:
            instance.password = hash(instance.password)

    @post_save.connect
    async def send_welcome_email(sender, instance, created, **kwargs):
        if created and sender.__name__ == "User":
            await send_email(instance.email, "Welcome!")
"""

from __future__ import annotations

import contextlib
import inspect
import logging
import weakref
from collections.abc import Callable
from typing import Any

logger = logging.getLogger("aquilia.models.signals")

__all__ = [
    "Signal",
    "pre_save",
    "post_save",
    "pre_delete",
    "post_delete",
    "pre_init",
    "post_init",
    "m2m_changed",
    "receiver",
    "class_prepared",
    "pre_migrate",
    "post_migrate",
]


class _DeadRef:
    """Sentinel indicating a weak reference that has been garbage-collected."""

    pass


class Signal:
    """
    A signal that can be connected to receiver functions.

    Receivers can be sync or async callables. They receive:
        sender   -- the Model class
        instance -- the model instance (if applicable)
        **kwargs -- signal-specific keyword arguments

    Features:
        - Sender-based filtering
        - Priority ordering (lower runs first)
        - Weak references (auto-disconnect when receiver is GC'd)
        - Temporary connections via context manager

    Usage:
        my_signal = Signal("my_signal")

        @my_signal.connect
        async def handler(sender, instance, **kwargs):
            print(f"Signal fired for {sender.__name__}")

        # Or connect without decorator
        my_signal.connect(handler)

        # Disconnect
        my_signal.disconnect(handler)

        # Fire
        await my_signal.send(MyModel, instance=obj, created=True)

        # Temporary connection
        async with my_signal.connected(handler):
            await my_signal.send(MyModel, instance=obj)
        # handler is automatically disconnected here
    """

    def __init__(self, name: str):
        """
        Create a new signal.

        Args:
            name: Human-readable identifier used in log messages, inspector
                trace spans, and ``repr()`` output. Not required to be
                globally unique, but by convention matches the module-level
                variable name (e.g. ``"pre_save"``).
        """
        self.name = name
        # Each entry: (receiver_or_weakref, sender_filter, priority)
        self._receivers: list[tuple] = []

    def connect(
        self,
        receiver: Callable = None,
        *,
        sender: type | None = None,
        weak: bool = False,
        priority: int = 100,
    ):
        """
        Connect a receiver function. Can be used as a decorator.

        Args:
            receiver: Callable to invoke when signal fires
            sender: Optional sender class to filter on
            weak: If True, store a weak reference (auto-cleanup on GC)
            priority: Lower values run first (default: 100)
        """

        def _decorator(fn: Callable) -> Callable:
            self._add_receiver(fn, sender, weak, priority)
            return fn

        if receiver is not None:
            # Called as @signal.connect (without parentheses)
            if callable(receiver):
                self._add_receiver(receiver, sender, weak, priority)
                return receiver
            # Called as @signal.connect(sender=MyModel)
            return _decorator
        return _decorator

    def _add_receiver(
        self,
        fn: Callable,
        sender: type | None,
        weak: bool,
        priority: int,
    ) -> None:
        """
        Internal: register a receiver, deduplicating by (function, sender).

        If ``weak`` is True, ``fn`` is wrapped in a ``weakref.ref`` carrying
        a finalizer (see ``_make_cleanup``) that prunes dead entries once
        ``fn`` is garbage collected; callables that cannot be weakly
        referenced (e.g. some builtins/bound methods of temporary objects)
        silently fall back to a strong reference instead of raising.

        Connecting the exact same ``(fn, sender)`` pair twice is a no-op --
        the existing entry is kept in place and no duplicate is appended,
        so decorating the same function twice with the same signal/sender
        has no extra effect.

        After insertion, ``_receivers`` is re-sorted by priority using
        Python's stable sort, so receivers with equal priority still run
        in the order they were connected.
        """
        # Store weak reference if requested
        if weak:
            try:
                ref = weakref.ref(fn, self._make_cleanup(fn, sender))
            except TypeError:
                # Built-in functions can't be weakly referenced
                ref = fn
        else:
            ref = fn

        # Check for duplicates (by identity)
        for existing_ref, existing_sender, _ in self._receivers:
            resolved = self._resolve_ref(existing_ref)
            if resolved is fn and existing_sender is sender:
                return  # Already connected

        self._receivers.append((ref, sender, priority))
        # Sort by priority (stable sort preserves insertion order for ties)
        self._receivers.sort(key=lambda x: x[2])

    def _make_cleanup(self, fn: Callable, sender: type | None) -> Callable:
        """
        Build the weakref finalizer invoked when a weakly-referenced
        receiver is garbage collected.

        Rather than locating and removing the single entry for ``fn``, the
        callback rebuilds ``_receivers`` filtering out every entry whose
        weakref has died -- simpler than tracking the specific tuple, and
        cheap given the typically small number of receivers per signal.
        The ``ref`` parameter (the now-dead weakref) is required by the
        ``weakref.ref(fn, callback)`` calling convention but is unused here.
        """

        def cleanup(ref):
            self._receivers = [(r, s, p) for r, s, p in self._receivers if self._resolve_ref(r) is not _DeadRef]

        return cleanup

    @staticmethod
    def _resolve_ref(ref: Any) -> Any:
        """Resolve a receiver -- dereference weakrefs."""
        if isinstance(ref, weakref.ref):
            obj = ref()
            if obj is None:
                return _DeadRef
            return obj
        return ref

    def disconnect(self, receiver: Callable, *, sender: type | None = None) -> bool:
        """
        Disconnect a receiver.

        First tries an exact match on ``(receiver, sender)``; if none is
        found (e.g. the receiver was connected without a sender filter, or
        with a different one), falls back to removing the first entry
        whose resolved callable is ``receiver`` regardless of its sender
        filter. Only one matching entry is removed per call.

        Args:
            receiver: The originally-connected callable (weak or strong).
            sender: The sender filter it was connected with, if any.

        Returns:
            True if a matching receiver was found and removed, False if
            no match exists (already disconnected, GC'd, or never
            connected).
        """
        for i, (ref, s, _p) in enumerate(self._receivers):
            resolved = self._resolve_ref(ref)
            if resolved is receiver and s is sender:
                self._receivers.pop(i)
                return True
        # Try removing without sender filter
        for i, (ref, s, _p) in enumerate(self._receivers):
            resolved = self._resolve_ref(ref)
            if resolved is receiver:
                self._receivers.pop(i)
                return True
        return False

    async def send(self, sender: type, **kwargs) -> list[Any]:
        """
        Fire the signal, invoking every connected receiver in priority order.

        Receivers are called lowest-``priority``-first (ties preserve
        connection order); dead weakrefs are skipped; receivers connected
        with a ``sender`` filter are skipped unless ``sender is filter_sender``
        (identity, not subclass, check). Coroutine-function receivers are
        awaited; plain callables are invoked directly (never offloaded to a
        thread), so a slow sync receiver blocks the whole ``send()``.

        A receiver raising is logged and does NOT stop the remaining
        receivers from running -- the exception instance itself is appended
        to the result list in place of a return value, so a single broken
        receiver can never prevent ``save()``/``delete()`` from completing.
        Inspect the returned list (or use :meth:`robust_send`, which pairs
        each result with its receiver) if you need to detect failures.

        When the Aquilia inspector is active, records a span on the
        ``Lane.SIGNALS`` lane covering the total dispatch time.

        Args:
            sender: The Model class sending the signal (passed to each
                receiver as the ``sender`` kwarg).
            **kwargs: Signal-specific arguments forwarded to every receiver
                (e.g. ``instance=``, ``created=``).

        Returns:
            One entry per matching, alive receiver: either its return
            value, or the ``Exception`` instance it raised.
        """
        t0 = None
        trace = None
        try:
            import time

            from aquilia.inspector.trace import current_trace

            trace = current_trace()
            if trace is not None:
                t0 = time.monotonic()
        except ImportError:
            pass

        results = []
        for ref, filter_sender, _ in self._receivers:
            receiver = self._resolve_ref(ref)
            if receiver is _DeadRef:
                continue
            # Skip if sender filter doesn't match
            if filter_sender is not None and sender is not filter_sender:
                continue
            try:
                if inspect.iscoroutinefunction(receiver):
                    result = await receiver(sender=sender, **kwargs)
                else:
                    result = receiver(sender=sender, **kwargs)
                results.append(result)
            except Exception as exc:
                logger.error(
                    f"Signal '{self.name}' receiver {receiver.__name__} raised {exc.__class__.__name__}: {exc}"
                )
                results.append(exc)

        if trace is not None and t0 is not None:
            try:
                import time

                from aquilia.inspector.trace import Lane, SpanStatus

                now_offset = (time.monotonic() - trace.started_monotonic) * 1000.0
                duration_ms = (time.monotonic() - t0) * 1000.0
                receiver_names = []
                for ref, filter_sender, _ in self._receivers:
                    r = self._resolve_ref(ref)
                    if r is not _DeadRef and (filter_sender is None or sender is filter_sender):
                        receiver_names.append(r.__name__ if hasattr(r, "__name__") else str(r))
                trace.add_span(
                    lane=Lane.SIGNALS,
                    label=f"Signal: {self.name} (from {sender.__name__ if hasattr(sender, '__name__') else str(sender)})",
                    start_offset_ms=max(0.0, now_offset - duration_ms),
                    duration_ms=duration_ms,
                    status=SpanStatus.OK,
                    detail={
                        "signal": self.name,
                        "sender": sender.__name__ if hasattr(sender, "__name__") else str(sender),
                        "receivers": receiver_names,
                    },
                )
            except Exception:
                pass

        return results

    def send_sync(self, sender: type, **kwargs) -> list[Any]:
        """
        Fire the signal synchronously, invoking only synchronous receivers.

        Behaves like :meth:`send` (priority order, sender filtering, dead
        weakrefs skipped, per-receiver exceptions logged and swallowed) but
        cannot ``await`` anything: any connected receiver that is a
        coroutine function is skipped with a logged warning instead of being
        called. Use this from non-async call sites (e.g. ``Model.__init__``
        for ``pre_init``/``post_init``) where there is no event loop to
        await into; async-only receivers on those signals simply never run.

        Returns:
            One entry per matching, alive, *synchronous* receiver invoked:
            either its return value, or the ``Exception`` it raised.
        """
        t0 = None
        trace = None
        try:
            import time

            from aquilia.inspector.trace import current_trace

            trace = current_trace()
            if trace is not None:
                t0 = time.monotonic()
        except ImportError:
            pass

        results = []
        for ref, filter_sender, _ in self._receivers:
            receiver = self._resolve_ref(ref)
            if receiver is _DeadRef:
                continue
            if filter_sender is not None and sender is not filter_sender:
                continue
            if inspect.iscoroutinefunction(receiver):
                logger.warning(f"Signal '{self.name}': async receiver {receiver.__name__} skipped in sync send")
                continue
            try:
                result = receiver(sender=sender, **kwargs)
                results.append(result)
            except Exception as exc:
                logger.error(
                    f"Signal '{self.name}' receiver {receiver.__name__} raised {exc.__class__.__name__}: {exc}"
                )
                results.append(exc)

        if trace is not None and t0 is not None:
            try:
                import time

                from aquilia.inspector.trace import Lane, SpanStatus

                now_offset = (time.monotonic() - trace.started_monotonic) * 1000.0
                duration_ms = (time.monotonic() - t0) * 1000.0
                receiver_names = []
                for ref, filter_sender, _ in self._receivers:
                    r = self._resolve_ref(ref)
                    if r is not _DeadRef and (filter_sender is None or sender is filter_sender):
                        if not inspect.iscoroutinefunction(r):
                            receiver_names.append(r.__name__ if hasattr(r, "__name__") else str(r))
                trace.add_span(
                    lane=Lane.SIGNALS,
                    label=f"Signal: {self.name} (from {sender.__name__ if hasattr(sender, '__name__') else str(sender)})",
                    start_offset_ms=max(0.0, now_offset - duration_ms),
                    duration_ms=duration_ms,
                    status=SpanStatus.OK,
                    detail={
                        "signal": self.name,
                        "sender": sender.__name__ if hasattr(sender, "__name__") else str(sender),
                        "receivers": receiver_names,
                    },
                )
            except Exception:
                pass

        return results

    async def robust_send(self, sender: type, **kwargs) -> list[Any]:
        """
        Fire the signal, invoking every connected receiver regardless of
        exceptions raised by earlier ones (the same fault-isolation
        behavior as :meth:`send`).

        The only difference from :meth:`send` is the shape of the return
        value: each entry is paired with the receiver that produced it, as
        ``(receiver, result_or_exception)``, instead of a flat list of
        values. Use ``robust_send`` when a caller needs to attribute a
        result or failure back to the specific receiver that produced it
        (e.g. surfacing per-handler errors in a debug/inspector view); use
        plain :meth:`send` when only the aggregate results matter.

        Returns:
            One ``(receiver, result_or_exception)`` tuple per matching,
            alive receiver, in the priority order they were invoked.
        """
        t0 = None
        trace = None
        try:
            import time

            from aquilia.inspector.trace import current_trace

            trace = current_trace()
            if trace is not None:
                t0 = time.monotonic()
        except ImportError:
            pass

        results = []
        for ref, filter_sender, _ in self._receivers:
            receiver = self._resolve_ref(ref)
            if receiver is _DeadRef:
                continue
            if filter_sender is not None and sender is not filter_sender:
                continue
            try:
                if inspect.iscoroutinefunction(receiver):
                    result = await receiver(sender=sender, **kwargs)
                else:
                    result = receiver(sender=sender, **kwargs)
                results.append((receiver, result))
            except Exception as exc:
                logger.error(
                    f"Signal '{self.name}' receiver {receiver.__name__} raised {exc.__class__.__name__}: {exc}"
                )
                results.append((receiver, exc))

        if trace is not None and t0 is not None:
            try:
                import time

                from aquilia.inspector.trace import Lane, SpanStatus

                now_offset = (time.monotonic() - trace.started_monotonic) * 1000.0
                duration_ms = (time.monotonic() - t0) * 1000.0
                receiver_names = []
                for ref, filter_sender, _ in self._receivers:
                    r = self._resolve_ref(ref)
                    if r is not _DeadRef and (filter_sender is None or sender is filter_sender):
                        receiver_names.append(r.__name__ if hasattr(r, "__name__") else str(r))
                trace.add_span(
                    lane=Lane.SIGNALS,
                    label=f"Signal: {self.name} (from {sender.__name__ if hasattr(sender, '__name__') else str(sender)})",
                    start_offset_ms=max(0.0, now_offset - duration_ms),
                    duration_ms=duration_ms,
                    status=SpanStatus.OK,
                    detail={
                        "signal": self.name,
                        "sender": sender.__name__ if hasattr(sender, "__name__") else str(sender),
                        "receivers": receiver_names,
                    },
                )
            except Exception:
                pass

        return results

    @property
    def receivers(self) -> list[Callable]:
        """List of connected receiver functions (resolved, alive only)."""
        result = []
        for ref, _, _ in self._receivers:
            resolved = self._resolve_ref(ref)
            if resolved is not _DeadRef:
                result.append(resolved)
        return result

    def has_listeners(self, sender: type | None = None) -> bool:
        """
        Check whether any (alive) receivers are connected.

        Args:
            sender: If given, only receivers connected with no sender
                filter, or whose filter is exactly this class (identity
                check, not subclass-aware), count as a match. If omitted,
                any alive receiver on this signal counts, regardless of
                each receiver's own sender filter.

        Returns:
            True if at least one matching, still-alive receiver exists.
        """
        if sender is None:
            return any(self._resolve_ref(ref) is not _DeadRef for ref, _, _ in self._receivers)
        return any(
            self._resolve_ref(ref) is not _DeadRef and (s is None or s is sender) for ref, s, _ in self._receivers
        )

    @contextlib.contextmanager
    def connected(self, fn: Callable, *, sender: type | None = None, priority: int = 100):
        """
        Context manager for temporary signal connection.

        The receiver is automatically disconnected on exit.

        Usage:
            with pre_save.connected(my_handler, sender=User):
                await user.save()
            # my_handler is disconnected here
        """
        self._add_receiver(fn, sender, weak=False, priority=priority)
        try:
            yield
        finally:
            self.disconnect(fn, sender=sender)

    def clear(self) -> None:
        """Remove all receivers (useful for testing)."""
        self._receivers.clear()

    def __repr__(self) -> str:
        """Return ``<Signal 'name' receivers=N>`` where N is the count of still-alive receivers."""
        alive = sum(1 for ref, _, _ in self._receivers if self._resolve_ref(ref) is not _DeadRef)
        return f"<Signal '{self.name}' receivers={alive}>"


# ── Built-in signals ─────────────────────────────────────────────────────────
#
# Every built-in signal is sent with `sender` set to the Model *subclass*
# involved (never an instance). Extra kwargs each receiver gets are
# documented below per-signal; find the actual `.send(...)` call sites in
# `aquilia/models/base.py`, `metaclass.py`, and `migration_runner.py`.

pre_save = Signal("pre_save")
"""Sent (async, via ``send()``) just before a row is INSERTed or UPDATEd.

Kwargs: ``instance`` (the model instance about to be saved), ``created``
(``True`` if this save will INSERT a new row, ``False`` if it will UPDATE
an existing one). Raising in a receiver propagates out of ``save()``
before any SQL has been executed for this call, aborting the save.
"""

post_save = Signal("post_save")
"""Sent (async, via ``send()``) after a row has been INSERTed or UPDATEd
and dirty-tracking has been reset.

Kwargs: ``instance`` (the saved model instance, with its primary key
populated for inserts), ``created`` (``True`` for an insert, ``False`` for
an update). Commonly used to enqueue follow-up work (e.g. welcome emails)
that should only happen once the row is durably written.
"""

pre_delete = Signal("pre_delete")
"""Sent (async, via ``send()``) before ``delete_instance()`` cascades
on_delete handling and issues the DELETE statement.

Kwargs: ``instance`` (the model instance about to be deleted; its primary
key is still populated). Fired outside the delete's transaction, so a
receiver cannot veto the delete by raising -- the exception is caught and
logged like any other signal receiver (see :meth:`Signal.send`).
"""

post_delete = Signal("post_delete")
"""Sent (async, via ``send()``) after the row (and any on_delete cascade
side effects) have been committed.

Kwargs: ``instance`` (the now-deleted model instance -- its primary key
attribute retains its prior value, but the row no longer exists in the
database).
"""

pre_init = Signal("pre_init")
"""Sent synchronously (via ``send_sync()``) at the start of ``Model.__init__``,
before field defaults/values are assigned onto the instance.

Kwargs: ``kwargs`` (the raw keyword arguments passed to the constructor,
as a dict). Only synchronous receivers run -- ``__init__`` cannot await,
so any async receiver connected to this signal is skipped with a warning.
"""

post_init = Signal("post_init")
"""Sent synchronously (via ``send_sync()``) at the end of ``Model.__init__``,
after all fields have been assigned.

Kwargs: ``instance`` (the newly-constructed model instance). Like
``pre_init``, async receivers are skipped with a warning since there is
no event loop to await into from ``__init__``.
"""

m2m_changed = Signal("m2m_changed")
"""Sent (async, via ``send()``) after a many-to-many relation is modified
via ``instance.attach(...)`` or ``instance.detach(...)``.

Kwargs: ``instance`` (the model instance the M2M field lives on),
``action`` (``"attach"`` or ``"detach"``), ``model`` (the M2M field name,
e.g. ``"tags"`` -- despite the name, this is the *field* name, not a
model class), ``pk_set`` (list of primary keys of the target objects that
were attached/detached). Fired after the junction-table rows have already
been written.
"""

class_prepared = Signal("class_prepared")
"""Sent synchronously (via ``send_sync()``) once per ``Model`` subclass,
from the metaclass, right after the class body has finished being
processed (fields collected, registered with ``ModelRegistry``, etc).

No extra kwargs -- ``sender`` is the newly-created model class. Useful for
registering per-model metadata that depends on the fully-assembled class
(e.g. building indexes) at import time, before any instances exist.
"""

pre_migrate = Signal("pre_migrate")
"""Sent (async, via ``send()``) before a migration run begins applying
pending migrations.

Kwargs: ``db`` (the database connection/engine the migration runner is
using). ``sender`` is the migration runner's class, not a ``Model``.
"""

post_migrate = Signal("post_migrate")
"""Sent (async, via ``send()``) after a migration run has finished
applying all pending migrations.

Kwargs: ``db`` (the database connection/engine used). ``sender`` is the
migration runner's class, not a ``Model``. Useful for seeding data or
warming caches once the schema is known to be up to date.
"""


# ── receiver() shorthand decorator ──────────────────────────────────────────


def receiver(signal: Signal, *, sender: type | None = None):
    """
    Shorthand decorator to connect a function to a signal.

    Usage:
        from aquilia.models.signals import receiver, pre_save

        @receiver(pre_save, sender=User)
        async def hash_password(sender, instance, **kwargs):
            if instance.password_changed:
                instance.password = hash(instance.password)

        # Multiple signals:
        @receiver(pre_save)
        @receiver(post_save)
        async def log_save(sender, instance, **kwargs):
            print(f"Saving {sender.__name__}")
    """

    def _decorator(fn: Callable) -> Callable:
        signal.connect(fn, sender=sender)
        return fn

    return _decorator
