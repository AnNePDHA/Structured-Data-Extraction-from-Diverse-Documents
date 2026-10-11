"""Abstract base pipeline with exponential backoff retry logic and rate-limit pacing."""

import random
import re
import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass
class ExtractionResult:
    """Result of one pipeline extraction call.

    Attributes:
        fields: Extracted field values, e.g. {"company": "...", "date": "..."}.
        usage: Token usage from the model API, e.g.
            {"prompt_tokens": 1234, "completion_tokens": 56, "total_tokens": 1290}.
            None if the call failed or the API did not return usage info.
        meta: Extra pipeline-specific info (e.g. OCR character count for OCR-LLM).
    """

    fields: dict
    usage: dict | None = None
    meta: dict = field(default_factory=dict)


logger = logging.getLogger(__name__)

# Exceptions that warrant a retry (rate limit / quota / transient server errors)
_RETRYABLE_MSGS = (
    "resource_exhausted",
    "rate limit",
    "quota",
    "too many requests",
    "429",
    "503",
    "deadline exceeded",
)


def _is_retryable(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(s in msg for s in _RETRYABLE_MSGS)


def _parse_retry_delay(exc: Exception) -> float | None:
    """Extract the server-suggested retry delay from a 429 error message.

    Gemini API includes either:
      "Please retry in 30.15s"          ← plain text format
      "retry_delay { seconds: 30 }"     ← proto format
    Returns the suggested seconds, or None if not found.
    """
    msg = str(exc)
    # Plain text: "Please retry in 30.158380632s"
    m = re.search(r"retry in\s+([\d.]+)s", msg, re.IGNORECASE)
    if m:
        return float(m.group(1))
    # Proto: "retry_delay {\n  seconds: 30\n}"
    m = re.search(r"retry_delay\s*\{[^}]*seconds:\s*(\d+)", msg)
    if m:
        return float(m.group(1))
    return None


class BasePipeline(ABC):
    """Base class for extraction pipelines.

    Provides:
    - Exponential-backoff retry on rate-limit errors (_call_with_retry)
    - Proactive pacing between API calls to stay under provider RPM (_pace)

    The actual model call is delegated to a ModelClient (see model_clients.py),
    so the same retry/pacing logic serves Gemini and Azure backends alike.
    """

    def __init__(self, client, min_interval_sec: float | None = None):
        """Initialize pipeline.

        Args:
            client: A ModelClient (Gemini or Azure) handling the generation call.
            min_interval_sec: Minimum seconds between API calls. Defaults to the
                client's own pacing (13s for free-tier Gemini, 0s for paid Azure).
        """
        self.client = client
        self.model = client.name
        self.min_interval_sec = (
            client.min_interval_sec if min_interval_sec is None else min_interval_sec
        )
        self._last_call_ts: float = 0.0

    @abstractmethod
    def extract(self, image_path: Path, fields: list[str]) -> ExtractionResult:
        """Extract fields from image. Returns ExtractionResult with fields + usage."""

    def _pace(self) -> None:
        """Sleep so that consecutive calls are spaced by at least min_interval_sec."""
        elapsed = time.perf_counter() - self._last_call_ts
        if elapsed < self.min_interval_sec:
            time.sleep(self.min_interval_sec - elapsed)
        self._last_call_ts = time.perf_counter()

    def _call_with_retry(
        self,
        fn: Callable,
        *args,
        max_retries: int = 5,
        base_delay: float = 2.0,
        **kwargs,
    ) -> Any:
        """Call fn(*args, **kwargs) with exponential backoff on rate-limit errors.

        Paces calls via _pace() before each attempt to proactively stay under
        rate limits. Delay on retry: base_delay * 2^attempt + uniform(0, 1) jitter.
        Non-retryable exceptions propagate immediately.
        """
        last_exc: Exception | None = None
        for attempt in range(max_retries + 1):
            self._pace()
            try:
                return fn(*args, **kwargs)
            except Exception as exc:
                if not _is_retryable(exc):
                    raise
                last_exc = exc
                if attempt == max_retries:
                    break
                # Prefer the server-suggested retry delay over our calculated one.
                # The API tells us exactly how long to wait — ignoring it causes
                # repeated 429s without making progress.
                server_delay = _parse_retry_delay(exc)
                calc_delay = base_delay * (2**attempt) + random.uniform(0, 1)
                delay = max(server_delay or 0.0, calc_delay)
                logger.warning(
                    "Rate limit hit (attempt %d/%d). Retrying in %.1fs "
                    "(server suggested: %s). Error: %s",
                    attempt + 1,
                    max_retries,
                    delay,
                    f"{server_delay:.0f}s" if server_delay else "n/a",
                    exc,
                )
                time.sleep(delay)
        raise RuntimeError(
            f"Max retries ({max_retries}) exceeded. Last error: {last_exc}"
        ) from last_exc
