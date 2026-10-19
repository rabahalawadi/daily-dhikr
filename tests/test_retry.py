"""
Tests for exponential backoff, jitter, and error retry policy.
"""

import pytest
from app.publishing.retry import is_retryable, calculate_backoff, ErrorCategory


def test_retryable_error_categories():
    """Network timeouts and rate limits should be retryable."""
    assert is_retryable(ErrorCategory.TRANSIENT_NETWORK) is True
    assert is_retryable(ErrorCategory.RATE_LIMITED) is True


def test_non_retryable_error_categories():
    """Permanent authentication failures and permission denials must NEVER be retried."""
    assert is_retryable(ErrorCategory.AUTHENTICATION_EXPIRED) is False
    assert is_retryable(ErrorCategory.PERMISSION_DENIED) is False
    assert is_retryable(ErrorCategory.INVALID_REQUEST) is False


def test_backoff_calculation_bounding():
    """Ensures backoff stays within minimum and maximum bounds."""
    for attempt in range(1, 6):
        delay = calculate_backoff(attempt=attempt, base_delay=2.0, max_delay=30.0)
        assert delay >= 2.0
        assert delay <= 30.0
