"""Tests for the checker module."""

from __future__ import annotations

from pathlib import Path

from pydocfix.checker import build_rules_map, check_file
from pydocfix.rules import PRM101, RTN101, SUM002
from pydocfix.rules.prm.prm001 import PRM001
from pydocfix.rules.rtn.rtn001 import RTN001


def _diagnose(filepath: Path, kind_map) -> list:
    source = filepath.read_text(encoding="utf-8")
    diags, *_ = check_file(source, filepath, kind_map)
    return diags


class TestDiagnoseFile:
    def test_detects_missing_period(self, tmp_path: Path):
        f = tmp_path / "example.py"
        f.write_text('def foo():\n    """Do something"""\n    pass\n')
        diags = _diagnose(f, build_rules_map([SUM002()]))
        assert len(diags) == 1
        assert diags[0].rule == "PDX-SUM002"
        assert diags[0].fixable is True

    def test_precise_range_for_summary(self, tmp_path: Path):
        f = tmp_path / "example.py"
        f.write_text('def foo():\n    """Do something"""\n    pass\n')
        diags = _diagnose(f, build_rules_map([SUM002()]))
        assert len(diags) == 1
        # "Do something" starts at line 2, col 8 (after triple-quote, 1-based)
        assert diags[0].lineno == 2
        assert diags[0].col == 8

    def test_no_violation_when_period(self, tmp_path: Path):
        f = tmp_path / "example.py"
        f.write_text('def foo():\n    """Do something."""\n    pass\n')
        diags = _diagnose(f, build_rules_map([SUM002()]))
        assert diags == []

    def test_no_docstring(self, tmp_path: Path):
        f = tmp_path / "example.py"
        f.write_text("def foo():\n    pass\n")
        diags = _diagnose(f, build_rules_map([SUM002()]))
        assert diags == []

    def test_multiple_functions(self, tmp_path: Path):
        f = tmp_path / "example.py"
        f.write_text('def foo():\n    """No period"""\n    pass\n\ndef bar():\n    """Has period."""\n    pass\n')
        diags = _diagnose(f, build_rules_map([SUM002()]))
        assert len(diags) == 1


class TestD401Integration:
    def test_param_type_mismatch(self, tmp_path: Path):
        f = tmp_path / "example.py"
        f.write_text(
            'def foo(x: int):\n    """Summary.\n\n    Args:\n        x (str): The x value.\n    """\n    pass\n'
        )
        diags = _diagnose(f, build_rules_map([PRM101()]))
        assert len(diags) == 1
        assert diags[0].rule == "PDX-PRM101"
        assert "'str'" in diags[0].message
        assert "'int'" in diags[0].message
        # TYPE token "str" is at line 5, col 12 (inside parentheses, 1-based)
        assert diags[0].lineno == 5
        assert diags[0].col == 12

    def test_return_type_mismatch(self, tmp_path: Path):
        f = tmp_path / "example.py"
        f.write_text(
            'def foo() -> int:\n    """Summary.\n\n    Returns:\n        str: The result.\n    """\n    pass\n'
        )
        diags = _diagnose(f, build_rules_map([RTN101()]))
        assert len(diags) == 1
        assert diags[0].rule == "PDX-RTN101"

    def test_no_mismatch(self, tmp_path: Path):
        f = tmp_path / "example.py"
        f.write_text(
            "def foo(x: int) -> bool:\n"
            '    """Summary.\n'
            "\n"
            "    Args:\n"
            "        x (int): The x value.\n"
            "\n"
            "    Returns:\n"
            "        bool: The result.\n"
            '    """\n'
            "    pass\n"
        )
        diags = _diagnose(f, build_rules_map([PRM101(), RTN101()]))
        assert diags == []

    def test_no_type_in_docstring(self, tmp_path: Path):
        f = tmp_path / "example.py"
        f.write_text('def foo(x: int):\n    """Summary.\n\n    Args:\n        x: The x value.\n    """\n    pass\n')
        diags = _diagnose(f, build_rules_map([PRM101()]))
        assert diags == []


class TestSyntaxErrorHandling:
    def test_syntax_error_returns_empty(self, tmp_path: Path):
        f = tmp_path / "bad.py"
        f.write_text("def foo(:\n    pass\n")
        diags = _diagnose(f, build_rules_map([SUM002()]))
        assert diags == []

    def test_syntax_error_does_not_raise(self, tmp_path: Path):
        f = tmp_path / "bad.py"
        f.write_text("class Foo(\n")
        # Should not raise
        diags = _diagnose(f, build_rules_map([SUM002()]))
        assert diags == []


class TestMultiSectionSimultaneousFix:
    def test_no_extra_blank_line_between_sections(self, tmp_path: Path):
        """Two section-insertion fixes applied at once must not produce a
        whitespace-only line between the two new sections."""
        import re

        src = (
            "def add(a: int, b: int) -> int:\n"
            '    """Add two numbers."""\n'
            "    return a + b\n"
        )
        _, fixed, _ = check_file(
            src,
            tmp_path / "add.py",
            build_rules_map([PRM001(), RTN001()]),
            fix=True,
            unsafe_fixes=True,
        )
        assert fixed is not None
        # Must not contain a whitespace-only line immediately followed by a
        # blank line (the artifact of two section_append_edit inserts).
        assert not re.search(r"\n[ \t]+\n\n", fixed)
        # Each section separator must be exactly one blank line.
        assert "\n\n\n" not in fixed
