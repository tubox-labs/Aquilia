"""HTTP security middleware.

One control per module. These were a single 1,100-line ``security.py``; CORS
and CSRF change for different reasons and get reviewed by different people, so
they get different files.

Registration order matters and is not cosmetic — see
:class:`aquilia.middleware.core.priority.Priority`. ``ProxyFixMiddleware`` must
precede anything IP-dependent, and ``CSRFMiddleware`` must follow the
authentication middleware whose session it reads.
"""

from aquilia.middleware.builtin.security.cors import CORSMiddleware
from aquilia.middleware.builtin.security.csp import CSPMiddleware, CSPPolicy
from aquilia.middleware.builtin.security.csrf import (
    CSRFError,
    CSRFMiddleware,
    csrf_exempt,
    csrf_token_func,
)
from aquilia.middleware.builtin.security.headers import SecurityHeadersMiddleware
from aquilia.middleware.builtin.security.hsts import HSTSMiddleware
from aquilia.middleware.builtin.security.https_redirect import HTTPSRedirectMiddleware
from aquilia.middleware.builtin.security.proxy_fix import ProxyFixMiddleware

__all__ = [
    "CORSMiddleware",
    "CSPMiddleware",
    "CSPPolicy",
    "CSRFError",
    "CSRFMiddleware",
    "HSTSMiddleware",
    "HTTPSRedirectMiddleware",
    "ProxyFixMiddleware",
    "SecurityHeadersMiddleware",
    "csrf_exempt",
    "csrf_token_func",
]
