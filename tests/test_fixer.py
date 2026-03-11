"""Tests for the fixer module."""

from __future__ import annotations

from pathlib import Path

from pydocfix.checker import build_kind_map, diagnose_file
from pydocfix.fixer import fix_file
from pydocfix.rules import D200


class TestFixFile:
    def test_fixes_missing_period(self, tmp_path: Path):
        f = tmp_path / "example.py"
        f.write_text('def foo():\n    """Do something"""\n    pass\n')
        diags = diagnose_file(f, build_kind_map([D200()]))
        result = fix_file(f, diags)
        assert result is not None
        assert '"""Do something."""' in result

    def test_no_fix_needed(self, tmp_path: Path):
        f = tmp_path / "example.py"
        f.write_text('def foo():\n    """Do something."""\n    pass\n')
        diags = diagnose_file(f, build_kind_map([D200()]))
        result = fix_file(f, diags)
        assert result is None

    def test_preserves_surrounding_code(self, tmp_path: Path):
        f = tmp_path / "example.py"
        src = 'x = 1\n\ndef foo():\n    """Do something"""\n    return x\n'
        f.write_text(src)
        diags = diagnose_file(f, build_kind_map([D200()]))
        result = fix_file(f, diags)
        assert result is not None
        assert "x = 1" in result
        assert "return x" in result
        assert '"""Do something."""' in result
