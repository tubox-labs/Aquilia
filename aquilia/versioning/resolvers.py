"""
Aquilia Versioning — Version Resolvers

Resolvers extract the raw version string from an incoming HTTP request.
Each resolver implements a single extraction strategy. Multiple resolvers
can be combined via ``CompositeResolver`` for fallback chains.

Built-in resolvers:
- URLPathResolver: ``/v2/users`` → "2"
- HeaderResolver: ``X-API-Version: 2.1`` → "2.1"
- QueryParamResolver: ``?api_version=2`` → "2"
- MediaTypeResolver: ``Accept: application/json; version=2`` → "2"
- ChannelResolver: ``X-API-Channel: stable`` → resolves to configured version
- CompositeResolver: tries resolvers in order, returns first match

Unlike DRF/NestJS which use a single resolver, Aquilia supports stacking
resolvers with priority and fallback, similar to ASP.NET API Versioning
but with channel-based resolution (unique to Aquilia).
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..request import Request


class BaseVersionResolver(ABC):
    """
    Abstract base class for version resolvers.

    A resolver extracts the raw version string (or channel name)
    from an HTTP request. It does NOT parse the version — that's
    handled by ``VersionParser``.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for this resolver."""
        ...

    @abstractmethod
    def resolve(self, request: Request) -> str | None:
        """
        Extract version string from request.

        Args:
            request: The incoming HTTP request.

        Returns:
            Raw version string, or ``None`` if not found.
        """
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


# ═══════════════════════════════════════════════════════════════════════════
#  URL Path Resolver
# ═══════════════════════════════════════════════════════════════════════════


class URLPathResolver(BaseVersionResolver):
    """
    Extract version from URL path segment.

    Matches patterns like ``/v1/...``, ``/v2.1/...``, ``/2025-01/...``.

    Configuration::

        URLPathResolver(
            segment_index=0,     # which path segment (0-based after prefix strip)
            prefix="v",          # expected prefix ('v', 'api-v', or '')
            strip_from_path=True # remove version segment from path for routing
        )

    Examples:
        ``/v2/users`` → "2"
        ``/v2.1/users`` → "2.1"
        ``/api-v3/users`` → "3" (with prefix="api-v")
    """

    def __init__(
        self,
        segment_index: int = 0,
        prefix: str = "v",
        strip_from_path: bool = True,
    ) -> None:
        self._segment_index = segment_index
        self._prefix = prefix.lower()
        self._strip_from_path = strip_from_path
        self._pattern = re.compile(
            rf"^{re.escape(self._prefix)}(\d+(?:\.\d+)*(?:-\d{{1,2}}(?:-\d{{1,2}})?)?)$",
            re.IGNORECASE,
        )

    @property
    def name(self) -> str:
        return "url_path"

    @property
    def strip_from_path(self) -> bool:
        return self._strip_from_path

    def resolve(self, request: Request) -> str | None:
        path = request.path if hasattr(request, "path") else "/"
        segments = [s for s in path.strip("/").split("/") if s]

        if len(segments) <= self._segment_index:
            return None

        segment = segments[self._segment_index]
        match = self._pattern.match(segment)
        if match:
            return match.group(1)
        return None

    def strip_version_from_path(self, path: str) -> str:
        """Remove the version segment from the path."""
        segments = [s for s in path.strip("/").split("/") if s]
        if len(segments) <= self._segment_index:
            return path

        segment = segments[self._segment_index]
        if self._pattern.match(segment):
            segments.pop(self._segment_index)
            stripped = "/" + "/".join(segments)
            return stripped if stripped != "/" or path == "/" else stripped
        return path


# ═══════════════════════════════════════════════════════════════════════════
#  Header Resolver
# ═══════════════════════════════════════════════════════════════════════════


class HeaderResolver(BaseVersionResolver):
    """
    Extract version from a custom HTTP header.

    Configuration::

        HeaderResolver(header_name="X-API-Version")

    Examples:
        ``X-API-Version: 2.1`` → "2.1"
        ``Api-Version: 3`` → "3"
    """

    def __init__(self, header_name: str = "X-API-Version") -> None:
        self._header_name = header_name.lower()

    @property
    def name(self) -> str:
        return "header"

    def resolve(self, request: Request) -> str | None:
        headers = request.headers if hasattr(request, "headers") else {}

        # Try exact match first
        if hasattr(headers, "get"):
            value = headers.get(self._header_name)
            if value:
                return value.strip()

        # Case-insensitive fallback
        if isinstance(headers, dict):
            for k, v in headers.items():
                if k.lower() == self._header_name:
                    return v.strip()

        return None

    def __repr__(self) -> str:
        return f"HeaderResolver(header_name={self._header_name!r})"


# ═══════════════════════════════════════════════════════════════════════════
#  Query Parameter Resolver
# ═══════════════════════════════════════════════════════════════════════════


class QueryParamResolver(BaseVersionResolver):
    """
    Extract version from query parameter.

    Configuration::

        QueryParamResolver(param_name="api_version")

    Examples:
        ``?api_version=2.1`` → "2.1"
        ``?version=3`` → "3" (with param_name="version")
    """

    def __init__(self, param_name: str = "api_version") -> None:
        self._param_name = param_name

    @property
    def name(self) -> str:
        return "query_param"

    def resolve(self, request: Request) -> str | None:
        # Try request.query_param() first (Aquilia API)
        if hasattr(request, "query_param"):
            value = request.query_param(self._param_name)
            if value:
                return value.strip()

        # Fallback to query_params dict
        if hasattr(request, "query_params"):
            qp = request.query_params
            if isinstance(qp, dict):
                value = qp.get(self._param_name)
                if isinstance(value, list) and value:
                    return value[0].strip()
                if isinstance(value, str) and value:
                    return value.strip()

        return None

    def __repr__(self) -> str:
        return f"QueryParamResolver(param_name={self._param_name!r})"


# ═══════════════════════════════════════════════════════════════════════════
#  Media Type Resolver
# ═══════════════════════════════════════════════════════════════════════════


class MediaTypeResolver(BaseVersionResolver):
    """
    Extract version from Accept header media type parameter.

    Parses ``Accept: application/json; version=2`` or
    ``Accept: application/vnd.myapp.v2+json``.

    Configuration::

        MediaTypeResolver(
            param_name="version",         # parameter name in media type
            vendor_pattern=None,          # regex for vendor media type
        )

    Examples:
        ``Accept: application/json; version=2`` → "2"
        ``Accept: application/vnd.aquilia.v2+json`` → "2"
    """

    _DEFAULT_VENDOR_RE = re.compile(
        r"application/vnd\.[^.]+\.v(\d+(?:\.\d+)*)\+",
        re.IGNORECASE,
    )

    def __init__(
        self,
        param_name: str = "version",
        vendor_pattern: str | None = None,
    ) -> None:
        self._param_name = param_name
        self._vendor_re = re.compile(vendor_pattern, re.IGNORECASE) if vendor_pattern else self._DEFAULT_VENDOR_RE

    @property
    def name(self) -> str:
        return "media_type"

    def resolve(self, request: Request) -> str | None:
        headers = request.headers if hasattr(request, "headers") else {}
        accept = None

        if hasattr(headers, "get"):
            accept = headers.get("accept")
        elif isinstance(headers, dict):
            for k, v in headers.items():
                if k.lower() == "accept":
                    accept = v
                    break

        if not accept:
            return None

        # Strategy 1: parameter-based (application/json; version=2)
        param_re = re.compile(
            rf"{re.escape(self._param_name)}\s*=\s*([^\s;,]+)",
            re.IGNORECASE,
        )
        param_match = param_re.search(accept)
        if param_match:
            return param_match.group(1).strip()

        # Strategy 2: vendor media type (application/vnd.app.v2+json)
        vendor_match = self._vendor_re.search(accept)
        if vendor_match:
            return vendor_match.group(1)

        return None


# ═══════════════════════════════════════════════════════════════════════════
#  Channel Resolver
# ═══════════════════════════════════════════════════════════════════════════


class ChannelResolver(BaseVersionResolver):
    """
    Resolve version via named channels (unique to Aquilia).

    Clients send a channel name (e.g. ``X-API-Channel: stable``)
    and the resolver maps it to the configured concrete version.

    This is a higher-level abstraction that lets API consumers
    express intent ("give me the stable version") rather than
    pinning to specific numbers.

    Configuration::

        ChannelResolver(
            header_name="X-API-Channel",
            channel_map={
                "stable": "2.0",
                "preview": "2.1",
                "legacy": "1.0",
            },
        )
    """

    def __init__(
        self,
        channel_map: dict[str, str] | None = None,
        header_name: str = "X-API-Channel",
        query_param: str = "api_channel",
    ) -> None:
        self._channel_map: dict[str, str] = channel_map or {}
        self._header_name = header_name.lower()
        self._query_param = query_param

    @property
    def name(self) -> str:
        return "channel"

    def resolve(self, request: Request) -> str | None:
        channel_name = self._extract_channel(request)
        if not channel_name:
            return None

        # Look up in channel map
        version_str = self._channel_map.get(channel_name.lower())
        return version_str

    def _extract_channel(self, request: Request) -> str | None:
        """Extract channel name from header or query param."""
        # Try header
        headers = request.headers if hasattr(request, "headers") else {}
        if hasattr(headers, "get"):
            value = headers.get(self._header_name)
            if value:
                return value.strip()

        # Case-insensitive header fallback
        if isinstance(headers, dict):
            for k, v in headers.items():
                if k.lower() == self._header_name:
                    return v.strip()

        # Try query param
        if hasattr(request, "query_param"):
            value = request.query_param(self._query_param)
            if value:
                return value.strip()

        return None

    def update_channel(self, channel: str, version: str) -> None:
        """Update channel → version mapping (for deployment-time changes)."""
        self._channel_map[channel.lower()] = version

    def __repr__(self) -> str:
        return f"ChannelResolver(channels={list(self._channel_map.keys())})"


# ═══════════════════════════════════════════════════════════════════════════
#  Composite Resolver
# ═══════════════════════════════════════════════════════════════════════════


class CompositeResolver(BaseVersionResolver):
    """
    Combine multiple resolvers with priority fallback.

    Tries each resolver in order and returns the first successful
    resolution. This enables stacking strategies, e.g.:

    1. Try URL path (``/v2/users``)
    2. Fall back to header (``X-API-Version: 2``)
    3. Fall back to query param (``?api_version=2``)
    4. Fall back to channel (``X-API-Channel: stable``)

    Configuration::

        CompositeResolver([
            URLPathResolver(),
            HeaderResolver(),
            QueryParamResolver(),
            ChannelResolver(channel_map={"stable": "2.0"}),
        ])
    """

    def __init__(self, resolvers: Sequence[BaseVersionResolver] | None = None) -> None:
        self._resolvers: list[BaseVersionResolver] = list(resolvers or [])

    @property
    def name(self) -> str:
        return "composite"

    def add(self, resolver: BaseVersionResolver) -> CompositeResolver:
        """Add a resolver to the chain."""
        self._resolvers.append(resolver)
        return self

    def resolve(self, request: Request) -> str | None:
        for resolver in self._resolvers:
            result = resolver.resolve(request)
            if result is not None:
                return result
        return None

    @property
    def resolvers(self) -> list[BaseVersionResolver]:
        """Get the resolver chain."""
        return list(self._resolvers)

    def get_url_resolver(self) -> URLPathResolver | None:
        """Get the URL path resolver (if any) for path stripping."""
        for r in self._resolvers:
            if isinstance(r, URLPathResolver):
                return r
        return None

    def __repr__(self) -> str:
        names = [r.name for r in self._resolvers]
        return f"CompositeResolver({names})"


# ═══════════════════════════════════════════════════════════════════════════
#  Custom Resolver (user-defined extraction logic)
# ═══════════════════════════════════════════════════════════════════════════


class CustomResolver(BaseVersionResolver):
    """
    User-defined version resolver.

    Wraps a callable that extracts the version from a request.

    Example::

        def extract_from_cookie(request):
            cookies = request.cookies
            return cookies.get("api_version")

        CustomResolver(extract_from_cookie, name="cookie")
    """

    def __init__(
        self,
        extractor: Callable[[Request], str | None],
        resolver_name: str = "custom",
    ) -> None:
        self._extractor = extractor
        self._name = resolver_name

    @property
    def name(self) -> str:
        return self._name

    def resolve(self, request: Request) -> str | None:
        try:
            return self._extractor(request)
        except Exception:
            return None
