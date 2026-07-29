"""
Backends package for aquilia.artifacts.

Provides pluggable storage backends:

- ``JSONFileBackend`` — default, generalised from ``JSONBytecodeCache``
- ``MemoryBackend``  — ephemeral/test use

``SQLiteBackend`` is reserved for future use (MCP knowledge index on large repos).
"""
