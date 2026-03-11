"""Tests for the checker module."""

from __future__ import annotations

from pathlib import Path

from pydocfix.checker import build_kind_map, diagnose_file
from pydocfix.rules import D200, D401


class TestDiagnoseFile:
    def test_detects_missing_period(self, tmp_path: Path):
        f = tmp_path / "example.py"
        f.write_text('def foo():\n    """Do something"""\n    pass\n')
        diags = diagnose_file(f, build_kind_map([D200()]))
        assert len(diags) == 1
        assert diags[0].rule == "D200"
        assert diags[0].fixable is True

    def test_precise_range_for_summary(self, tmp_path: Path):
        f = tmp_path / "example.py"
        f.write_text('def foo():\n    """Do something"""\n    pass\n')
        diags = diagnose_file(f, build_kind_map([D200()]))
        assert len(diags) == 1
        # "Do something" starts at line 2, col 7 (after triple-quote)
        assert diags[0].line == 2
        assert diags[0].col == 7

    def test_no_violation_when_period(self, tmp_path: Path):
        f = tmp_path / "example.py"
        f.write_text('def foo():\n    """Do something."""\n    pass\n')
        diags = diagnose_file(f, build_kind_map([D200()]))
        assert diags == []

    def test_no_docstring(self, tmp_path: Path):
        f = tmp_path / "example.py"
        f.write_text("def foo():\n    pass\n")
        diags = diagnose_file(f, build_kind_map([D200()]))
        assert diags == []

    def test_multiple_functions(self, tmp_path: Path):
        f = tmp_path / "example.py"
        f.write_text('def foo():\n    """No period"""\n    pass\n\ndef bar():\n    """Has period."""\n    pass\n')
        diags = diagnose_file(f, build_kind_map([D200()]))
        assert len(diags) == 1


class TestD401Integration:
    def test_param_type_mismatch(self, tmp_path: Path):
        f = tmp_path / "example.py"
        f.write_text(
            'def foo(x: int):\n    """Summary.\n\n    Args:\n        x (str): The x value.\n    """\n    pass\n'
        )
        diags = diagnose_file(f, build_kind_map([D401()]))
        assert len(diags) == 1
        assert diags[0].rule == "D401"
        assert "'str'" in diags[0].message
        assert "'int'" in diags[0].message
        # TYPE token "str" is at line 5, col 11 (inside parentheses)
        assert diags[0].line == 5
        assert diags[0].col == 11

    def test_return_type_mismatch(self, tmp_path: Path):
        f = tmp_path / "example.py"
        f.write_text(
            'def foo() -> int:\n    """Summary.\n\n    Returns:\n        str: The result.\n    """\n    pass\n'
        )
        diags = diagnose_file(f, build_kind_map([D401()]))
        assert len(diags) == 1
        assert diags[0].rule == "D401"

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
        diags = diagnose_file(f, build_kind_map([D401()]))
        assert diags == []

    def test_no_type_in_docstring(self, tmp_path: Path):
        f = tmp_path / "example.py"
        f.write_text('def foo(x: int):\n    """Summary.\n\n    Args:\n        x: The x value.\n    """\n    pass\n')
        diags = diagnose_file(f, build_kind_map([D401()]))
        assert diags == []
