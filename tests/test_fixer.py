"""Tests for the fixer module."""

from __future__ import annotations

from pathlib import Path

from pydocfix.checker import build_rules_map, diagnose_file
from pydocfix.fixer import fix_file
from pydocfix.rules import (
    Applicability,
    D200,
    Diagnostic,
    Edit,
    Fix,
    Offset,
    Range,
)


class TestFixFile:
    def test_fixes_missing_period(self, tmp_path: Path):
        f = tmp_path / "example.py"
        f.write_text('def foo():\n    """Do something"""\n    pass\n')
        diags = diagnose_file(f, build_rules_map([D200()]))
        result = fix_file(f, diags)
        assert result is not None
        assert '"""Do something."""' in result

    def test_no_fix_needed(self, tmp_path: Path):
        f = tmp_path / "example.py"
        f.write_text('def foo():\n    """Do something."""\n    pass\n')
        diags = diagnose_file(f, build_rules_map([D200()]))
        result = fix_file(f, diags)
        assert result is None

    def test_preserves_surrounding_code(self, tmp_path: Path):
        f = tmp_path / "example.py"
        src = 'x = 1\n\ndef foo():\n    """Do something"""\n    return x\n'
        f.write_text(src)
        diags = diagnose_file(f, build_rules_map([D200()]))
        result = fix_file(f, diags)
        assert result is not None
        assert "x = 1" in result
        assert "return x" in result
        assert '"""Do something."""' in result

    def test_overlapping_fixes_skips_later(self, tmp_path: Path):
        """When two Fixes target overlapping byte ranges, the second is skipped."""
        f = tmp_path / "example.py"
        f.write_text('def foo():\n    """Hello"""\n    pass\n')

        dummy_range = Range(start=Offset(2, 4), end=Offset(2, 15))
        # Fix A: replace "Hello" (bytes 0-5) with "Hi"
        fix_a = Fix(edits=[Edit(start=0, end=5, new_text="Hi")], applicability=Applicability.SAFE)
        diag_a = Diagnostic(
            rule="RA",
            message="a",
            filepath=str(f),
            range=dummy_range,
            docstring_line=2,
            fix=fix_a,
        )
        # Fix B: replace "Hel" (bytes 0-3) with "Bye" — overlaps with Fix A
        fix_b = Fix(edits=[Edit(start=0, end=3, new_text="Bye")], applicability=Applicability.SAFE)
        diag_b = Diagnostic(
            rule="RB",
            message="b",
            filepath=str(f),
            range=dummy_range,
            docstring_line=2,
            fix=fix_b,
        )

        result = fix_file(f, [diag_a, diag_b])
        assert result is not None
        # Fix A wins, Fix B is skipped
        assert '"""Hi"""' in result
