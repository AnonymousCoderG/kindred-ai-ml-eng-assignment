"""Error types that separate retryable LLM failures from permanent ones."""


class LLMError(Exception):
    pass


class TransientLLMError(LLMError):
    """Worth retrying: rate limit (429), server error (5xx), timeout, network."""

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class PermanentLLMError(LLMError):
    """Not worth retrying: bad request (400), bad key (401/403), unparseable output."""


class ExtractionFailed(LLMError):
    """Transient errors persisted until the retry budget was used up."""
