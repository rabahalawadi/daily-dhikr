"""
Retry strategies, backoff logic, and API error classification for Instagram publishing.
Guarantees sensitive secrets (access tokens) are never leaked in logs or error traces.
"""

import math
import random
import re
import time
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Token redaction regex
TOKEN_REGEX = re.compile(r"(access_token=)([a-zA-Z0-9_\-\.]+)", re.IGNORECASE)
BEARER_REGEX = re.compile(r"(Bearer\s+)([a-zA-Z0-9_\-\.]+)", re.IGNORECASE)


def redact_sensitive_info(message: str) -> str:
    """Replaces access tokens and sensitive credentials with [REDACTED]."""
    if not message:
        return ""
    redacted = TOKEN_REGEX.sub(r"\1[REDACTED]", str(message))
    redacted = BEARER_REGEX.sub(r"\1[REDACTED]", redacted)
    return redacted


class ErrorCategory:
    TRANSIENT_NETWORK = "TRANSIENT_NETWORK"
    RATE_LIMITED = "RATE_LIMITED"
    AUTHENTICATION_EXPIRED = "AUTHENTICATION_EXPIRED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    AMBIGUOUS_TIMEOUT = "AMBIGUOUS_TIMEOUT"
    INVALID_REQUEST = "INVALID_REQUEST"
    CONTAINER_FAILED = "CONTAINER_FAILED"
    UNKNOWN = "UNKNOWN"


def classify_meta_error(status_code: Optional[int], error_data: Optional[dict], exception: Optional[Exception] = None) -> Tuple[str, str]:
    """
    Classifies a Meta Graph API error response into an actionable category.
    Returns: (error_category, clean_redacted_message)
    """
    if exception is not None:
        exc_str = str(exception)
        if "timeout" in exc_str.lower() or "timed out" in exc_str.lower():
            return ErrorCategory.AMBIGUOUS_TIMEOUT, redact_sensitive_info(exc_str)
        if "connection" in exc_str.lower() or "connecterror" in exc_str.lower():
            return ErrorCategory.TRANSIENT_NETWORK, redact_sensitive_info(exc_str)

    if not error_data or "error" not in error_data:
        if status_code and status_code >= 500:
            return ErrorCategory.TRANSIENT_NETWORK, f"Meta server returned 5xx status: {status_code}"
        return ErrorCategory.UNKNOWN, f"Unknown error (status {status_code})"

    meta_err = error_data.get("error", {})
    code = meta_err.get("code")
    subcode = meta_err.get("error_subcode")
    msg = meta_err.get("message", "No message provided")
    redacted_msg = redact_sensitive_info(f"Code {code} (subcode {subcode}): {msg}")

    # Meta Error Code Classification
    # 190 = Invalid OAuth access token / expired
    if code == 190:
        return ErrorCategory.AUTHENTICATION_EXPIRED, redacted_msg

    # 10, 200 = Permission denied / missing scope
    if code in (10, 200) or subcode in (458, 459, 460, 463, 467):
        return ErrorCategory.PERMISSION_DENIED, redacted_msg

    # 4, 17, 32, 613 = Rate limit hit
    if code in (4, 17, 32, 613):
        return ErrorCategory.RATE_LIMITED, redacted_msg

    # Server side temporary issues
    if code in (1, 2) or (status_code and status_code >= 500):
        return ErrorCategory.TRANSIENT_NETWORK, redacted_msg

    return ErrorCategory.INVALID_REQUEST, redacted_msg


def is_retryable(error_category: str) -> bool:
    """
    Determines if an error is transient and safe to retry.
    Permanent failures (expired token, lack of permissions, invalid content) are NEVER retried.
    """
    return error_category in (
        ErrorCategory.TRANSIENT_NETWORK,
        ErrorCategory.RATE_LIMITED,
    )


def calculate_backoff(attempt: int, base_delay: float = 5.0, max_delay: float = 60.0) -> float:
    """
    Calculates bounded exponential backoff with full jitter:
    delay = random_between(0, min(max_delay, base_delay * (2 ** attempt)))
    """
    upper_bound = min(max_delay, base_delay * (2 ** attempt))
    return random.uniform(base_delay, upper_bound)
