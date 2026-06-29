"""Strict newline-delimited JSON-RPC socket transport."""

from __future__ import annotations

import json
import signal
import socket
import sys
import threading
from typing import Any

from ..protocol import PARSE_ERROR, error_response, fault_to_error, parse_request, success_response


class SocketTransport:
    """Read JSON-RPC requests from a TCP socket and write responses."""

    def __init__(self, server: Any, host: str = "127.0.0.1", port: int = 8765) -> None:
        self.server = server
        self.host = host
        self.port = port
        self._stopping = False
        self.server_socket: socket.socket | None = None
        self.clients: set[socket.socket] = set()
        self.lock = threading.Lock()

    def serve(self) -> None:
        # Print beautiful startup messages to stderr (clean and premium, no icons)
        sys.stderr.write("\n")
        sys.stderr.write("   ========================================================\n")
        sys.stderr.write("   AQUILIA MCP SOCKET SERVER STARTED\n")
        sys.stderr.write("   ========================================================\n")
        sys.stderr.write(f"   Workspace:  {self.server.config.root}\n")
        sys.stderr.write(f"   Tools:      {len(self.server.registry.list_tools())} active\n")
        sys.stderr.write(f"   Prompts:    {len(self.server.registry.list_prompts())} active\n")
        sys.stderr.write(f"   Transport:  SOCKET (TCP)\n")
        sys.stderr.write(f"   Address:    {self.host}:{self.port}\n")
        sys.stderr.write("   Status:     Listening for connections...\n")
        sys.stderr.write("   ========================================================\n")
        sys.stderr.write("   Press Ctrl+C to stop.\n\n")
        sys.stderr.flush()

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(128)
        except Exception as exc:
            sys.stderr.write(f"   Error: Failed to bind socket to {self.host}:{self.port}: {exc}\n\n")
            sys.stderr.flush()
            return

        old_sigint = None
        old_sigterm = None

        def _handle_signal(signum, frame):
            raise KeyboardInterrupt()

        try:
            old_sigint = signal.signal(signal.SIGINT, _handle_signal)
        except ValueError:
            pass

        try:
            old_sigterm = signal.signal(signal.SIGTERM, _handle_signal)
        except ValueError:
            pass

        try:
            while not self._stopping:
                try:
                    self.server_socket.settimeout(0.5)
                    client_sock, client_addr = self.server_socket.accept()
                    with self.lock:
                        self.clients.add(client_sock)
                    thread = threading.Thread(target=self._handle_client, args=(client_sock,), daemon=True)
                    thread.start()
                except socket.timeout:
                    continue
                except (socket.error, ValueError):
                    break
        except (KeyboardInterrupt, SystemExit):
            self._stopping = True
        finally:
            self._cleanup(old_sigint, old_sigterm)

    def _cleanup(self, old_sigint: Any, old_sigterm: Any) -> None:
        self._stopping = True
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass

        # Close all active clients
        with self.lock:
            for client in list(self.clients):
                try:
                    client.close()
                except Exception:
                    pass
            self.clients.clear()

        # Restore signal handlers
        if old_sigint is not None:
            try:
                signal.signal(signal.SIGINT, old_sigint)
            except Exception:
                pass
        if old_sigterm is not None:
            try:
                signal.signal(signal.SIGTERM, old_sigterm)
            except Exception:
                pass

        sys.stderr.write("\n   Aquilia MCP Socket Server shutting down...\n")
        sys.stderr.write("   Server terminated.\n\n")
        sys.stderr.flush()

    def _handle_client(self, client_sock: socket.socket) -> None:
        from .stdio import StdioTransport
        stdio_helper = StdioTransport(self.server)

        buffer = ""
        try:
            while not self._stopping:
                data = client_sock.recv(4096)
                if not data:
                    break
                buffer += data.decode("utf-8", errors="replace")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    response = stdio_helper.handle_line(line)
                    if response is not None:
                        payload = json.dumps(response, separators=(",", ":"), sort_keys=True) + "\n"
                        client_sock.sendall(payload.encode("utf-8"))
        except Exception:
            pass
        finally:
            try:
                client_sock.close()
            except Exception:
                pass
            with self.lock:
                self.clients.discard(client_sock)
