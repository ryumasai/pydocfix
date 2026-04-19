"""Tests for edit creation and application — D-1 to D-6."""

from __future__ import annotations

import pytest

from pydocfix.edits import apply_edits, detect_section_indent
from pydocfix.models import Edit


class TestApplyEdits:
    """D-1 to D-4: apply_edits()."""

    def test_single_edit(self):
        """D-1: a single edit is applied correctly."""
        result = apply_edits("Hello world.", [Edit(start=0, end=5, new_text="Hi")])

        assert result == "Hi world."

    def test_multiple_non_overlapping_edits(self):
        """D-2: multiple non-overlapping edits are applied in reverse order."""
        result = apply_edits(
            "Hello world.",
            [
                Edit(start=6, end=11, new_text="there"),
                Edit(start=0, end=5, new_text="Hi"),
            ],
        )

        assert result == "Hi there."

    def test_overlapping_edits_raise(self):
        """D-3: overlapping edits raise ValueError."""
        with pytest.raises(ValueError, match="[Oo]verlap"):
            apply_edits(
                "Hello",
                [Edit(start=0, end=3, new_text="A"), Edit(start=2, end=4, new_text="B")],
            )

    def test_utf8_multibyte_characters(self):
        """D-4: byte offsets are respected for multibyte UTF-8 characters."""
        # "こんにちは" = 5 chars × 3 bytes each = 15 bytes
        result = apply_edits("こんにちは world", [Edit(start=0, end=15, new_text="Hello")])

        assert result == "Hello world"


class TestDetectSectionIndent:
    """D-5 to D-6: detect_section_indent()."""

    def test_single_line_uses_col_offset(self):
        """D-5: single-line docstring returns stmt_col_offset spaces."""
        result = detect_section_indent("Summary text.", stmt_col_offset=4)

        assert result == "    "

    def test_multiline_with_trailing_blank_line(self):
        """D-6: multiline docstring with trailing whitespace-only line returns that line."""
        text = "Summary.\n\n    Args:\n        x: int.\n    "
        result = detect_section_indent(text)

        assert result == "    "
