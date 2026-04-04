"""
AquilaHTTP — Retry Strategies.

Configurable retry logic with exponential backoff, jitter,
and condition-based retry decisions.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeVar

from .config import RetryConfig
from .faults import (
    ConnectionClosedFault,
    ConnectionFault,
    HTTPClientFault,
    RetryExhaustedFault,
    TimeoutFault,
)
from .request import HTTPClientRequest
from .response import HTTPClientResponse

logger = logging.getLogger("aquilia.http.retry")

T = TypeVar("T")


@dataclass
class RetryState:
    """State tracking for retry attempts."""

    attempt: int = 0
    last_error: Exception | None = None
    last_response: HTTPClientResponse | None = None
    total_delay: float = 0.0
    start_time: float = 0.0

    @property
    def elapsed(self) -> float:
        """Total elapsed time since first attempt."""
        if self.start_time == 0:
            return 0.0
        return time.monotonic() - self.start_time


class RetryStrategy(ABC):
    """
    Abstract retry strategy.

    Subclasses define retry conditions and backoff calculation.
    """

    @abstractmethod
    def should_retry(
        self,
        state: RetryState,
        request: HTTPClientRequest,
        response: HTTPClientResponse | None,
        error: Exception | None,
    ) -> bool:
        """
        Determine if request should be retried.

        Args:
            state: Current retry state.
            request: The request being retried.
            response: Response if received (may be None).
            error: Error if raised (may be None).

        Returns:
            True if retry should be attempted.
        """
        ...

    @abstractmethod
    def get_delay(self, state: RetryState) -> float:
        """
        Calculate delay before next retry.

        Args:
            state: Current retry state.

        Returns:
            Delay in seconds.
        """
        ...


class ExponentialBackoff(RetryStrategy):
    """
    Exponential backoff retry strategy.

    Delay increases exponentially with optional jitter.
    """

    __slots__ = ("_config",)

    def __init__(self, config: RetryConfig | None = None):
        self._config = config or RetryConfig()

    @property
    def config(self) -> RetryConfig:
        return self._config

    def should_retry(
        self,
        state: RetryState,
        request: HTTPClientRequest,
        response: HTTPClientResponse | None,
        error: Exception | None,
    ) -> bool:
        """Check if retry should be attempted."""
        # Check attempt limit
        if state.attempt >= self._config.max_attempts:
            return False

        # Check if method is retryable
        if request.method.value not in self._config.retry_on_methods:
            # POST is not retryable by default (not idempotent)
            return False

        # Retry on specific errors
        if error is not None:
            if isinstance(error, (ConnectionFault, TimeoutFault, ConnectionClosedFault)):
                return True
            if isinstance(error, HTTPClientFault) and error.retryable:
                return True
            return False

        # Retry on specific status codes
        if response is not None:
            return response.status_code in self._config.retry_on_status

        return False

    def get_delay(self, state: RetryState) -> float:
        """Calculate exponential backoff delay."""
        base_delay = self._config.backoff_base * (self._config.backoff_multiplier**state.attempt)

        # Cap at max delay
        delay = min(base_delay, self._config.backoff_max)

        # Add jitter
        if self._config.backoff_jitter > 0:
            jitter = delay * self._config.backoff_jitter * random.random()
            delay += jitter

        return delay


class ConstantBackoff(RetryStrategy):
    """
    Constant delay retry strategy.

    Same delay between all retries.
    """

    __slots__ = ("_delay", "_max_attempts", "_retry_on_status", "_retry_on_methods")

    def __init__(
        self,
        delay: float = 1.0,
        max_attempts: int = 3,
        retry_on_status: frozenset[int] | None = None,
        retry_on_methods: frozenset[str] | None = None,
    ):
        self._delay = delay
        self._max_attempts = max_attempts
        self._retry_on_status = retry_on_status or frozenset({429, 500, 502, 503, 504})
        self._retry_on_methods = retry_on_methods or frozenset({"GET", "HEAD", "OPTIONS", "PUT", "DELETE"})

    def should_retry(
        self,
        state: RetryState,
        request: HTTPClientRequest,
        response: HTTPClientResponse | None,
        error: Exception | None,
    ) -> bool:
        if state.attempt >= self._max_attempts:
            return False

        if request.method.value not in self._retry_on_methods:
            return False

        if error is not None:
            if isinstance(error, (ConnectionFault, TimeoutFault, ConnectionClosedFault)):
                return True
            if isinstance(error, HTTPClientFault) and error.retryable:
                return True
            return False

        if response is not None:
            return response.status_code in self._retry_on_status

        return False

    def get_delay(self, state: RetryState) -> float:
        return self._delay


class NoRetry(RetryStrategy):
    """No retry strategy - never retries."""

    def should_retry(
        self,
        state: RetryState,
        request: HTTPClientRequest,
        response: HTTPClientResponse | None,
        error: Exception | None,
    ) -> bool:
        return False

    def get_delay(self, state: RetryState) -> float:
        return 0.0


class RetryAfterStrategy(RetryStrategy):
    """
    Strategy that respects Retry-After header.

    Uses server-specified delay when available.
    """

    __slots__ = ("_fallback", "_max_wait")

    def __init__(
        self,
        fallback: RetryStrategy | None = None,
        max_wait: float = 120.0,
    ):
        self._fallback = fallback or ExponentialBackoff()
        self._max_wait = max_wait

    def should_retry(
        self,
        state: RetryState,
        request: HTTPClientRequest,
        response: HTTPClientResponse | None,
        error: Exception | None,
    ) -> bool:
        return self._fallback.should_retry(state, request, response, error)

    def get_delay(self, state: RetryState) -> float:
        if state.last_response is not None:
            retry_after = state.last_response.get_header("Retry-After")
            if retry_after:
                try:
                    # Try as seconds
                    delay = float(retry_after)
                    return min(delay, self._max_wait)
                except ValueError:
                    # Try as HTTP date
                    try:
                        from email.utils import parsedate_to_datetime

                        retry_date = parsedate_to_datetime(retry_after)
                        delay = (retry_date - retry_date.now(retry_date.tzinfo)).total_seconds()
                        return min(max(0, delay), self._max_wait)
                    except (TypeError, ValueError):
                        pass

        return self._fallback.get_delay(state)


class CompositeRetryStrategy(RetryStrategy):
    """
    Composite strategy combining multiple strategies.

    Retries if ANY strategy says to retry.
    """

    __slots__ = ("_strategies",)

    def __init__(self, strategies: list[RetryStrategy]):
        self._strategies = strategies

    def should_retry(
        self,
        state: RetryState,
        request: HTTPClientRequest,
        response: HTTPClientResponse | None,
        error: Exception | None,
    ) -> bool:
        return any(s.should_retry(state, request, response, error) for s in self._strategies)

    def get_delay(self, state: RetryState) -> float:
        # Use maximum delay from all strategies
        if not self._strategies:
            return 0.0
        return max(s.get_delay(state) for s in self._strategies)


class RetryExecutor:
    """
    Executes operations with retry logic.

    Wraps async operations with configurable retry handling.
    """

    __slots__ = ("_strategy",)

    def __init__(self, strategy: RetryStrategy | None = None):
        self._strategy = strategy or ExponentialBackoff()

    async def execute(
        self,
        operation: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]],
        request: HTTPClientRequest,
    ) -> HTTPClientResponse:
        """
        Execute operation with retries.

        Args:
            operation: Async operation to execute.
            request: Request to send.

        Returns:
            Response from successful operation.

        Raises:
            RetryExhaustedFault: If all retries are exhausted.
            HTTPClientFault: If a non-retryable error occurs.
        """
        state = RetryState(start_time=time.monotonic())

        while True:
            state.attempt += 1
            response: HTTPClientResponse | None = None
            error: Exception | None = None

            try:
                response = await operation(request)
                state.last_response = response

                # Check if response requires retry
                if not self._strategy.should_retry(state, request, response, None):
                    return response

            except Exception as e:
                error = e
                state.last_error = e

                # Check if error is retryable
                if not self._strategy.should_retry(state, request, None, error):
                    raise

            # Calculate delay and wait
            delay = self._strategy.get_delay(state)
            state.total_delay += delay

            logger.debug(f"Retry attempt {state.attempt}, delay={delay:.2f}s, url={request.url}")

            await asyncio.sleep(delay)

        # Should not reach here, but handle edge case
        raise RetryExhaustedFault(
            f"All retry attempts exhausted after {state.attempt} attempts",
            attempts=state.attempt,
            last_error=str(state.last_error) if state.last_error else "",
            url=request.url,
        )


def create_retry_strategy(config: RetryConfig | None = None) -> RetryStrategy:
    """
    Create a retry strategy from configuration.

    Args:
        config: Retry configuration.

    Returns:
        Configured retry strategy.
    """
    if config is None:
        return ExponentialBackoff()

    if config.max_attempts == 0:
        return NoRetry()

    return RetryAfterStrategy(
        fallback=ExponentialBackoff(config),
        max_wait=config.backoff_max,
    )
