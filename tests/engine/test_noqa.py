"""Tests for noqa directive parsing — A-1 to A-11."""

from __future__ import annotations

from pydocfix.noqa import NoqaDirective, find_inline_noqa, parse_file_noqa, parse_inline_noqa


class TestNoqaDirective:
    """A-6, A-7: NoqaDirective.suppresses()."""

    def test_blanket_suppresses_any_code(self):
        """A-6: codes=None suppresses any rule code."""
        d = NoqaDirective(codes=None)

        assert d.suppresses("SUM001")
        assert d.suppresses("ANYTHING123")

    def test_specific_suppresses_listed_only(self):
        """A-7: codes=frozenset(...) suppresses listed codes and not others."""
        d = NoqaDirective(codes=frozenset({"PRM001"}))

        assert d.suppresses("PRM001")
        assert not d.suppresses("SUM001")


class TestParseInlineNoqa:
    """A-1 to A-5: parse_inline_noqa()."""

    def test_blanket_noqa(self):
        """A-1: bare # noqa returns codes=None."""
        result = parse_inline_noqa('    """docstring"""  # noqa')

        assert result is not None
        assert result.codes is None

    def test_single_code(self):
        """A-2: # noqa: PRM001 returns frozenset with one code."""
        result = parse_inline_noqa('    """docstring"""  # noqa: PRM001')

        assert result is not None
        assert result.codes == frozenset({"PRM001"})

    def test_multiple_codes(self):
        """A-3: # noqa: PRM001, SUM002 returns both codes."""
        result = parse_inline_noqa('    """docstring"""  # noqa: PRM001, SUM002')

        assert result is not None
        assert result.codes == frozenset({"PRM001", "SUM002"})

    def test_case_insensitive(self):
        """A-4: # NOQA is recognised regardless of case."""
        result = parse_inline_noqa('    """docstring"""  # NOQA')

        assert result is not None
        assert result.codes is None

    def test_no_noqa_returns_none(self):
        """A-5: line without noqa returns None."""
        result = parse_inline_noqa('    """docstring"""')

        assert result is None


class TestFindInlineNoqa:
    """A-11 to A-13: find_inline_noqa() span and return value."""

    def test_returns_directive_and_span(self):
        """A-11: returns (directive, (start, end)) when noqa present."""
        line = '    """docstring"""  # noqa: SUM001'
        result = find_inline_noqa(line)

        assert result is not None
        directive, (start, end) = result
        assert directive.codes == frozenset({"SUM001"})
        assert start < end

    def test_no_noqa_returns_none(self):
        """A-12: returns None when no noqa present."""
        result = find_inline_noqa('    """docstring"""')

        assert result is None

    def test_span_within_line(self):
        """A-13: span positions are within the line boundaries."""
        line = '    """docstring"""  # noqa'
        result = find_inline_noqa(line)

        assert result is not None
        _, (start, end) = result
        assert 0 <= start < end <= len(line)


class TestParseFileNoqa:
    """A-8 to A-11 (file-level): parse_file_noqa()."""

    def test_blanket_file_noqa(self):
        """A-8: # pydocfix: noqa on its own line returns blanket directive."""
        lines = ["# pydocfix: noqa\n", "def foo():\n", '    """doc"""\n']
        result = parse_file_noqa(lines)

        assert result is not None
        assert result.codes is None

    def test_specific_file_noqa(self):
        """A-9: # pydocfix: noqa: SUM001 returns directive with that code."""
        lines = ["# pydocfix: noqa: SUM001\n", "def foo():\n"]
        result = parse_file_noqa(lines)

        assert result is not None
        assert result.codes == frozenset({"SUM001"})

    def test_inline_after_code_not_recognised(self):
        """A-10: directive after code on the same line is not file-level."""
        lines = ["x = 1  # pydocfix: noqa\n"]
        result = parse_file_noqa(lines)

        assert result is None

    def test_no_directive_returns_none(self):
        """A-11: returns None when no file-level directive exists."""
        lines = ["def foo():\n", '    """doc"""\n']
        result = parse_file_noqa(lines)

        assert result is None
