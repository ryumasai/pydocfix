"""Tests for noqa directive parsing and suppression."""

from __future__ import annotations

from pathlib import Path

import pytest

from pydocfix.checker import build_rules_map, check_file
from pydocfix.noqa import NoqaDirective, parse_file_noqa, parse_inline_noqa
from pydocfix.rules import SUM002
from pydocfix.rules.prm.prm001 import PRM001
from pydocfix.rules.rtn.rtn001 import RTN001
from pydocfix.rules.sum.sum002 import SUM002

# ---------------------------------------------------------------------------
# Unit tests for parse_inline_noqa
# ---------------------------------------------------------------------------


class TestParseInlineNoqa:
    def test_no_noqa_returns_none(self):
        assert parse_inline_noqa('    """Docstring."""') is None

    def test_blanket_noqa(self):
        result = parse_inline_noqa('    """Docstring."""  # noqa')
        assert result is not None
        assert result.codes is None

    def test_blanket_noqa_uppercase(self):
        result = parse_inline_noqa('    """Docstring."""  # NOQA')
        assert result is not None
        assert result.codes is None

    def test_blanket_noqa_no_space(self):
        result = parse_inline_noqa('    """Docstring."""  #noqa')
        assert result is not None
        assert result.codes is None

    def test_single_code(self):
        result = parse_inline_noqa('    """Docstring."""  # noqa: SUM002')
        assert result is not None
        assert result.codes == frozenset({"SUM002"})

    def test_multiple_codes_comma(self):
        result = parse_inline_noqa('    """Docstring."""  # noqa: PRM001, SUM002')
        assert result is not None
        assert result.codes == frozenset({"PRM001", "SUM002"})

    def test_multiple_codes_no_space(self):
        result = parse_inline_noqa('    """Docstring."""  # noqa: PRM001,SUM002')
        assert result is not None
        assert result.codes == frozenset({"PRM001", "SUM002"})

    def test_code_lowercase_normalised(self):
        result = parse_inline_noqa('    """Docstring."""  # noqa: sum002')
        assert result is not None
        assert result.codes == frozenset({"SUM002"})

    def test_suppresses_all_when_blanket(self):
        directive = NoqaDirective(codes=None)
        assert directive.suppresses("PRM001")
        assert directive.suppresses("SUM002")
        assert directive.suppresses("RTN101")

    def test_suppresses_only_listed_codes(self):
        directive = NoqaDirective(codes=frozenset({"PRM001"}))
        assert directive.suppresses("PRM001")
        assert not directive.suppresses("SUM002")

    def test_suppresses_case_insensitive(self):
        directive = NoqaDirective(codes=frozenset({"PRM001"}))
        assert directive.suppresses("prm001")
        assert directive.suppresses("PRM001")


# ---------------------------------------------------------------------------
# Unit tests for parse_file_noqa
# ---------------------------------------------------------------------------


class TestParseFileNoqa:
    def test_no_directive_returns_none(self):
        lines = ["def foo():\n", '    """Docstring."""\n']
        assert parse_file_noqa(lines) is None

    def test_blanket_file_noqa(self):
        lines = ["# pydocfix: noqa\n", "def foo():\n", '    """Docstring."""\n']
        result = parse_file_noqa(lines)
        assert result is not None
        assert result.codes is None

    def test_file_noqa_with_code(self):
        lines = ["# pydocfix: noqa: SUM002\n", "def foo():\n"]
        result = parse_file_noqa(lines)
        assert result is not None
        assert result.codes == frozenset({"SUM002"})

    def test_file_noqa_case_insensitive(self):
        lines = ["# PYDOCFIX: NOQA\n"]
        result = parse_file_noqa(lines)
        assert result is not None
        assert result.codes is None

    def test_file_noqa_not_matched_after_code(self):
        # Must be on its own line — following code means it's inline, not file-level
        lines = ["x = 1  # pydocfix: noqa\n"]
        # This should NOT be matched as a file-level directive
        result = parse_file_noqa(lines)
        assert result is None

    def test_multiple_codes(self):
        lines = ["# pydocfix: noqa: PRM001, SUM002\n"]
        result = parse_file_noqa(lines)
        assert result is not None
        assert result.codes == frozenset({"PRM001", "SUM002"})


# ---------------------------------------------------------------------------
# Integration tests in check_file
# ---------------------------------------------------------------------------


class TestInlineNoqaIntegration:
    def test_blanket_noqa_suppresses_all(self, tmp_path: Path):
        f = tmp_path / "example.py"
        # Single-line docstring: closing """ is on the same line
        f.write_text('def foo():\n    """No period"""  # noqa\n    pass\n')
        diags, *_ = check_file(f.read_text(), f, build_rules_map([SUM002()]))
        assert diags == []

    def test_specific_code_noqa_suppresses_only_that_rule(self, tmp_path: Path):
        f = tmp_path / "example.py"
        f.write_text('def foo():\n    """No period"""  # noqa: SUM002\n    pass\n')
        diags, *_ = check_file(f.read_text(), f, build_rules_map([SUM002()]))
        assert diags == []

    def test_wrong_code_noqa_does_not_suppress(self, tmp_path: Path):
        f = tmp_path / "example.py"
        f.write_text('def foo():\n    """No period"""  # noqa: PRM001\n    pass\n')
        diags, *_ = check_file(f.read_text(), f, build_rules_map([SUM002()]))
        # SUM002 violation + NOQ001 for unused PRM001
        rules = {d.rule for d in diags}
        assert "SUM002" in rules
        assert "NOQ001" in rules

    def test_multiline_docstring_noqa_on_closing_line(self, tmp_path: Path):
        f = tmp_path / "example.py"
        src = 'def foo():\n    """No period\n\n    """  # noqa: SUM002\n    pass\n'
        f.write_text(src)
        diags, *_ = check_file(f.read_text(), f, build_rules_map([SUM002()]))
        assert diags == []

    def test_noqa_on_def_line_does_not_suppress(self, tmp_path: Path):
        # noqa on the def line should NOT suppress docstring violations
        f = tmp_path / "example.py"
        f.write_text('def foo():  # noqa: SUM002\n    """No period"""\n    pass\n')
        diags, *_ = check_file(f.read_text(), f, build_rules_map([SUM002()]))
        assert len(diags) == 1

    def test_noqa_suppressed_diagnostic_also_skips_fix(self, tmp_path: Path):
        f = tmp_path / "example.py"
        f.write_text('def foo():\n    """No period"""  # noqa\n    pass\n')
        diags, fixed, remaining = check_file(f.read_text(), f, build_rules_map([SUM002()]), fix=True)
        assert diags == []
        assert fixed is None
        assert remaining == []

    def test_per_function_noqa(self, tmp_path: Path):
        """noqa on one function's docstring should not affect another."""
        f = tmp_path / "example.py"
        src = 'def foo():\n    """No period"""  # noqa\n    pass\n\ndef bar():\n    """Also no period"""\n    pass\n'
        f.write_text(src)
        diags, *_ = check_file(f.read_text(), f, build_rules_map([SUM002()]))
        assert len(diags) == 1
        assert diags[0].rule == "SUM002"


class TestFileNoqaIntegration:
    def test_file_level_blanket_suppresses_all(self, tmp_path: Path):
        f = tmp_path / "example.py"
        src = (
            "# pydocfix: noqa\n"
            "def foo():\n"
            '    """No period"""\n'
            "    pass\n"
            "\n"
            "def bar():\n"
            '    """Also no period"""\n'
            "    pass\n"
        )
        f.write_text(src)
        diags, *_ = check_file(f.read_text(), f, build_rules_map([SUM002()]))
        assert diags == []

    def test_file_level_specific_code_suppresses_only_that_rule(self, tmp_path: Path):
        f = tmp_path / "example.py"
        src = '# pydocfix: noqa: SUM002\ndef foo():\n    """No period"""\n    pass\n'
        f.write_text(src)
        diags, *_ = check_file(f.read_text(), f, build_rules_map([SUM002()]))
        assert diags == []

    def test_file_level_wrong_code_does_not_suppress(self, tmp_path: Path):
        f = tmp_path / "example.py"
        src = '# pydocfix: noqa: PRM001\ndef foo():\n    """No period"""\n    pass\n'
        f.write_text(src)
        diags, *_ = check_file(f.read_text(), f, build_rules_map([SUM002()]))
        assert len(diags) == 1
        assert diags[0].rule == "SUM002"

    def test_file_level_suppresses_all_docstrings(self, tmp_path: Path):
        f = tmp_path / "example.py"
        src = (
            "# pydocfix: noqa\n"
            "def foo():\n"
            '    """No period"""\n'
            "    pass\n"
            "\n"
            "class Bar:\n"
            '    """Also no period"""\n'
            "\n"
            "    def baz(self):\n"
            '        """Still no period"""\n'
            "        pass\n"
        )
        f.write_text(src)
        diags, *_ = check_file(f.read_text(), f, build_rules_map([SUM002()]))
        assert diags == []


# ---------------------------------------------------------------------------
# NOQ001: Unused noqa directive
# ---------------------------------------------------------------------------


class TestNOQ001:
    def test_blanket_noqa_suppresses_real_violation_no_noq001(self, tmp_path: Path):
        """Blanket # noqa that actually suppresses something is NOT reported."""
        f = tmp_path / "example.py"
        f.write_text('def foo():\n    """No period"""  # noqa\n    pass\n')
        diags, *_ = check_file(f.read_text(), f, build_rules_map([SUM002()]))
        assert not any(d.rule == "NOQ001" for d in diags)

    def test_blanket_noqa_suppresses_nothing_is_reported(self, tmp_path: Path):
        """Blanket # noqa on a docstring with no violations → NOQ001."""
        f = tmp_path / "example.py"
        f.write_text('def foo():\n    """No period."""  # noqa\n    pass\n')
        diags, *_ = check_file(f.read_text(), f, build_rules_map([SUM002()]))
        assert len(diags) == 1
        assert diags[0].rule == "NOQ001"
        assert diags[0].message == "Unused `noqa` directive"

    def test_specific_code_used_no_noq001(self, tmp_path: Path):
        """# noqa: SUM002 that actually suppresses SUM002 is NOT reported."""
        f = tmp_path / "example.py"
        f.write_text('def foo():\n    """No period"""  # noqa: SUM002\n    pass\n')
        diags, *_ = check_file(f.read_text(), f, build_rules_map([SUM002()]))
        assert not any(d.rule == "NOQ001" for d in diags)

    def test_specific_code_unused_is_reported(self, tmp_path: Path):
        """# noqa: SUM002 when SUM002 doesn't fire → NOQ001."""
        f = tmp_path / "example.py"
        f.write_text('def foo():\n    """Has a period."""  # noqa: SUM002\n    pass\n')
        diags, *_ = check_file(f.read_text(), f, build_rules_map([SUM002()]))
        assert len(diags) == 1
        assert diags[0].rule == "NOQ001"
        assert "SUM002" in diags[0].message

    def test_multiple_codes_one_unused(self, tmp_path: Path):
        """# noqa: SUM002, PRM001 when only SUM002 fires → NOQ001 for PRM001 only."""
        f = tmp_path / "example.py"
        f.write_text('def foo():\n    """No period"""  # noqa: SUM002, PRM001\n    pass\n')
        diags, *_ = check_file(f.read_text(), f, build_rules_map([SUM002(), PRM001()]))
        noq = [d for d in diags if d.rule == "NOQ001"]
        assert len(noq) == 1
        assert "PRM001" in noq[0].message

    def test_non_pydocfix_code_ignored(self, tmp_path: Path):
        """# noqa: SUM002, pylint-something — non-pydocfix codes are not flagged."""
        f = tmp_path / "example.py"
        # pylint000 doesn't match pydocfix code pattern so it won't appear in ALL_RULE_CODES
        f.write_text('def foo():\n    """No period."""  # noqa: SUM002, RTN001\n    pass\n')
        diags, *_ = check_file(f.read_text(), f, build_rules_map([SUM002()]))
        # SUM002 is unused, RTN001 is known to pydocfix but also unused
        noq_codes = {d.rule for d in diags if d.rule == "NOQ001"}
        assert "NOQ001" in noq_codes

    def test_fix_removes_blanket_noqa(self, tmp_path: Path):
        """--fix removes a blanket # noqa that suppresses nothing."""
        f = tmp_path / "example.py"
        f.write_text('def foo():\n    """Has a period."""  # noqa\n    pass\n')
        diags, fixed, remaining = check_file(f.read_text(), f, build_rules_map([SUM002()]), fix=True)
        assert fixed is not None
        assert "# noqa" not in fixed
        assert remaining == []

    def test_fix_removes_specific_unused_code(self, tmp_path: Path):
        """--fix removes an unused specific code, leaving the comment clean."""
        f = tmp_path / "example.py"
        f.write_text('def foo():\n    """Has a period."""  # noqa: SUM002\n    pass\n')
        diags, fixed, remaining = check_file(f.read_text(), f, build_rules_map([SUM002()]), fix=True)
        assert fixed is not None
        assert "# noqa" not in fixed

    def test_fix_rewrites_partial_noqa(self, tmp_path: Path):
        """--fix rewrites # noqa: SUM002, PRM001 → # noqa: SUM002 when PRM001 unused."""
        f = tmp_path / "example.py"
        f.write_text('def foo():\n    """No period"""  # noqa: SUM002, PRM001\n    pass\n')
        diags, fixed, remaining = check_file(f.read_text(), f, build_rules_map([SUM002(), PRM001()]), fix=True)
        assert fixed is not None
        assert "# noqa: SUM002" in fixed
        assert "PRM001" not in fixed

    def test_noq001_lineno_points_to_noqa_line(self, tmp_path: Path):
        """NOQ001's line number should match the closing \"\"\" line."""
        f = tmp_path / "example.py"
        f.write_text('def foo():\n    """Has period."""  # noqa: SUM002\n    pass\n')
        diags, *_ = check_file(f.read_text(), f, build_rules_map([SUM002()]))
        noq = next(d for d in diags if d.rule == "NOQ001")
        assert noq.lineno == 2  # the closing `"""` is on line 2
