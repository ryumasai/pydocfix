"""Tests for noqa directive parsing."""

from __future__ import annotations

import pytest

from pydocfix.noqa import NoqaDirective, find_inline_noqa, parse_file_noqa, parse_inline_noqa


class TestParseInlineNoqa:
    """Tests for parse_inline_noqa()."""

    def test_no_noqa(self):
        """Returns None when no noqa directive."""
        assert parse_inline_noqa('    """docstring"""') is None

    def test_blanket_noqa(self):
        """Returns blanket NoqaDirective for bare noqa."""
        result = parse_inline_noqa('    """docstring"""  # noqa')

        assert result is not None
        assert result.codes is None
        assert result.suppresses("SUM001")
        assert result.suppresses("PRM001")

    def test_specific_codes(self):
        """Returns directive with specific codes."""
        result = parse_inline_noqa('    """docstring"""  # noqa: SUM001, SUM002')

        assert result is not None
        assert result.codes == frozenset({"SUM001", "SUM002"})
        assert result.suppresses("SUM001")
        assert not result.suppresses("PRM001")

    def test_single_code(self):
        """Returns directive with single code."""
        result = parse_inline_noqa('    """docstring"""  # noqa: PRM001')

        assert result is not None
        assert result.codes == frozenset({"PRM001"})


class TestParseFileNoqa:
    """Tests for parse_file_noqa()."""

    def test_no_directive(self):
        """Returns None when no file-level directive."""
        lines = ["def foo():\n", '    """docstring"""\n']

        assert parse_file_noqa(lines) is None

    def test_blanket_file_noqa(self):
        """Returns blanket directive for file-level noqa."""
        lines = ["# pydocfix: noqa\n", "def foo():\n", '    """doc"""\n']

        result = parse_file_noqa(lines)

        assert result is not None
        assert result.codes is None
        assert result.suppresses("SUM001")

    def test_specific_file_noqa(self):
        """Returns directive with specific codes for file-level noqa."""
        lines = ["# pydocfix: noqa: SUM001, PRM001\n", "def foo():\n"]

        result = parse_file_noqa(lines)

        assert result is not None
        assert result.codes == frozenset({"SUM001", "PRM001"})

    def test_inline_noqa_not_counted(self):
        """Inline noqa after code is not treated as file-level."""
        lines = ["x = 1  # pydocfix: noqa\n"]

        result = parse_file_noqa(lines)

        assert result is None


class TestNoqaDirective:
    """Tests for NoqaDirective."""

    def test_blanket_suppresses_all(self):
        """Blanket directive suppresses any code."""
        d = NoqaDirective(codes=None)

        assert d.suppresses("SUM001")
        assert d.suppresses("ANYTHING123")

    def test_specific_suppresses_listed(self):
        """Specific codes directive only suppresses listed."""
        d = NoqaDirective(codes=frozenset({"SUM001"}))

        assert d.suppresses("SUM001")
        assert not d.suppresses("PRM001")
