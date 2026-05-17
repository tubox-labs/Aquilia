"""Strict newline-delimited JSON-RPC stdio transport."""

from __future__ import annotations

import json
import signal
import sys
from typing import Any, TextIO

from ..protocol import (
    PARSE_ERROR,
    error_response,
    fault_to_error,
    parse_request,
    success_response,
)


class StdioTransport:
    """Read JSON-RPC requests from stdin and write responses to stdout."""

    def __init__(
        self,
        server: Any,
        *,
        stdin: TextIO | None = None,
        stdout: TextIO | None = None,
        max_request_bytes: int = 1_000_000,
    ) -> None:
        self.server = server
        self.stdin = stdin or sys.stdin
        self.stdout = stdout or sys.stdout
        self.max_request_bytes = max_request_bytes
        self._stopping = False

    def serve(self) -> None:
        old_handler = signal.getsignal(signal.SIGINT)

        def _handle_sigint(signum, frame):
            self._stopping = True

        try:
            signal.signal(signal.SIGINT, _handle_sigint)
        except ValueError:
            old_handler = None

        try:
            while not self._stopping:
                line = self.stdin.readline()
                if line == "":
                    break
                response = self.handle_line(line)
                if response is not None:
                    self._write(response)
        finally:
            if old_handler is not None:
                with _suppress_signal_error():
                    signal.signal(signal.SIGINT, old_handler)

    def handle_line(self, line: str) -> dict[str, Any] | None:
        if not line.strip():
            return None
        if len(line.encode("utf-8", errors="replace")) > self.max_request_bytes:
            return error_response(None, PARSE_ERROR, "JSON-RPC frame exceeds configured maximum size")
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            return error_response(None, PARSE_ERROR, f"Malformed JSON: {exc.msg}")
        request_id = payload.get("id") if isinstance(payload, dict) else None
        try:
            request = parse_request(payload)
            result = self.server.handle(request.method, request.params)
            if result is None or request.notification:
                return None
            return success_response(request.id, result)
        except Exception as exc:
            code, message, data = fault_to_error(exc)
            return error_response(request_id, code, message, data=data)

    def _write(self, response: dict[str, Any]) -> None:
        self.stdout.write(json.dumps(response, separators=(",", ":"), sort_keys=True) + "\n")
        self.stdout.flush()


class _suppress_signal_error:
    def __enter__(self):
        return None

    def __exit__(self, exc_type, exc, tb):
        return exc_type is ValueError
