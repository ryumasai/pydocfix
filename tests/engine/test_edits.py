"""Tests for edit creation and application."""

from __future__ import annotations

import pytest

from pydocfix.edits import apply_edits, delete_range, detect_section_indent, insert_at, section_append_edit
from pydocfix.models import Edit


class TestApplyEdits:
    """apply_edits()."""

    def test_empty_edits_returns_original(self):
        """empty edit list returns the original string unchanged."""
        result = apply_edits("Hello world.", [])

        assert result == "Hello world."

    def test_single_edit(self):
        """a single edit is applied correctly."""
        result = apply_edits("Hello world.", [Edit(start=0, end=5, new_text="Hi")])

        assert result == "Hi world."

    def test_multiple_non_overlapping_edits(self):
        """multiple non-overlapping edits are applied in reverse order."""
        result = apply_edits(
            "Hello world.",
            [
                Edit(start=6, end=11, new_text="there"),
                Edit(start=0, end=5, new_text="Hi"),
            ],
        )

        assert result == "Hi there."

    def test_overlapping_edits_raise(self):
        """overlapping edits raise ValueError."""
        with pytest.raises(ValueError, match="[Oo]verlap"):
            apply_edits(
                "Hello",
                [Edit(start=0, end=3, new_text="A"), Edit(start=2, end=4, new_text="B")],
            )

    def test_utf8_multibyte_characters(self):
        """byte offsets are respected for multibyte UTF-8 characters."""
        # "こんにちは" = 5 chars × 3 bytes each = 15 bytes
        result = apply_edits("こんにちは world", [Edit(start=0, end=15, new_text="Hello")])

        assert result == "Hello world"


class TestHelperFactories:
    """insert_at(), delete_range() factory helpers."""

    def test_insert_at_zero(self):
        """insert_at(0, text) inserts at the start."""
        edit = insert_at(0, "Hi ")
        result = apply_edits("world", [edit])

        assert result == "Hi world"

    def test_delete_range(self):
        """delete_range removes the specified byte span."""
        edit = delete_range(5, 11)
        result = apply_edits("Hello world!", [edit])

        assert result == "Hello!"


class TestSectionAppendEdit:
    """section_append_edit()."""

    def test_appends_to_multiline_docstring(self):
        """section is inserted before trailing indent in a multiline docstring."""
        ds_text = "Summary.\n\n    "
        root_end = len(ds_text.encode("utf-8"))
        edit = section_append_edit(ds_text, root_end, "    Returns:\n        None.")

        result = apply_edits(ds_text, [edit])

        assert "Returns:" in result
        assert result.endswith("    ")  # closing indent preserved

    def test_appends_to_single_line_docstring(self):
        """section is appended with blank-line separator for single-line docstring."""
        ds_text = "Summary."
        root_end = len(ds_text.encode("utf-8"))
        edit = section_append_edit(ds_text, root_end, "    Returns:\n        None.")

        result = apply_edits(ds_text, [edit])

        assert "Returns:" in result
        assert "\n\n" in result  # blank line separator


class TestDetectSectionIndent:
    """detect_section_indent()."""

    def test_single_line_uses_col_offset(self):
        """single-line docstring returns stmt_col_offset spaces."""
        result = detect_section_indent("Summary text.", stmt_col_offset=4)

        assert result == "    "

    def test_multiline_with_trailing_blank_line(self):
        """multiline docstring with trailing whitespace-only line returns that line."""
        text = "Summary.\n\n    Args:\n        x: int.\n    "
        result = detect_section_indent(text)

        assert result == "    "
