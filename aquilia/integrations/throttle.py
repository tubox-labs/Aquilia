from dataclasses import dataclass


@dataclass
class ThrottleConfig:
    backend: str = "memory"
    default_limit: int = 100
    default_window: int = 60
    key_prefix: str = "aq:throttle:"
    fail_open: bool = True
    max_clients: int = 10000
