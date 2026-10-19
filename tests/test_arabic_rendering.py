"""
Tests for Arabic text shaping, right-to-left BiDi reordering, and unicode validation.
"""

import pytest
from app.graphics.fonts import shape_arabic_text, get_arabic_font
from app.content.verification import contains_arabic, compute_arabic_checksum


def test_arabic_regex_detection():
    """Verifies that Arabic text is properly detected and English text without Arabic is rejected."""
    assert contains_arabic("سُبْحَانَ اللَّهِ") is True
    assert contains_arabic("الحمد لله رب العالمين") is True
    assert contains_arabic("Just plain English text") is False
    assert contains_arabic("1234567890") is False


def test_arabic_shaping_preserves_content():
    """Ensures Arabic shaping produces non-empty display text."""
    raw = "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ"
    shaped = shape_arabic_text(raw)
    assert shaped != ""
    assert len(shaped) > 0


def test_arabic_checksum_consistency():
    """Verifies that normalized text produces identical checksums regardless of whitespace."""
    text1 = "سُبْحَانَ اللَّهِ   وَبِحَمْدِهِ"
    text2 = " سُبْحَانَ اللَّهِ وَبِحَمْدِهِ "
    assert compute_arabic_checksum(text1) == compute_arabic_checksum(text2)


def test_arabic_font_loading():
    """Verifies that font loader returns a valid font instance without crashing."""
    font = get_arabic_font(size=40)
    assert font is not None
