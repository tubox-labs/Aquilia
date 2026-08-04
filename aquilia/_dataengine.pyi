"""Type stubs for the native data engine extension.

Hand-written rather than generated: the module is small, and the stub doubles as
the authoritative description of the boundary API.
"""

def noop() -> None:
    """Do nothing. Used to measure the Python<->native call cost."""
