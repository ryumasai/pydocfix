"""Tests for the check_file fix integration."""

from __future__ import annotations

from pathlib import Path

from pydocfix.checker import build_rules_map, check_file
from pydocfix.config import Config
from pydocfix.rules import (
    DOC001,
    PRM001,
    PRM005,
    PRM006,
    RTN001,
    SUM002,
)


class TestCheckFileFix:
    def test_fixes_missing_period(self, tmp_path: Path):
        f = tmp_path / "example.py"
        src = 'def foo():\n    """Do something"""\n    pass\n'
        f.write_text(src)
        _, result, _ = check_file(src, f, build_rules_map([SUM002()]), fix=True)
        assert result is not None
        assert '"""Do something."""' in result

    def test_no_fix_needed(self, tmp_path: Path):
        f = tmp_path / "example.py"
        src = 'def foo():\n    """Do something."""\n    pass\n'
        f.write_text(src)
        _, result, _ = check_file(src, f, build_rules_map([SUM002()]), fix=True)
        assert result is None

    def test_preserves_surrounding_code(self, tmp_path: Path):
        f = tmp_path / "example.py"
        src = 'x = 1\n\ndef foo():\n    """Do something"""\n    return x\n'
        f.write_text(src)
        _, result, _ = check_file(src, f, build_rules_map([SUM002()]), fix=True)
        assert result is not None
        assert "x = 1" in result
        assert "return x" in result
        assert '"""Do something."""' in result

    def test_no_fix_without_flag(self, tmp_path: Path):
        f = tmp_path / "example.py"
        src = 'def foo():\n    """Do something"""\n    pass\n'
        f.write_text(src)
        diags, result, _ = check_file(src, f, build_rules_map([SUM002()]))
        assert len(diags) == 1
        assert result is None  # fix=False by default

    def test_diagnostics_returned_with_fix(self, tmp_path: Path):
        f = tmp_path / "example.py"
        src = 'def foo():\n    """Do something"""\n    pass\n'
        f.write_text(src)
        diags, result, _ = check_file(src, f, build_rules_map([SUM002()]), fix=True)
        assert len(diags) == 1
        assert diags[0].rule == "SUM002"
        assert result is not None


class TestIterativeFix:
    """Tests for the iterative fix loop that resolves overlapping edits."""

    def test_overlapping_fixes_resolved_across_iterations(self, tmp_path: Path):
        """PRM005 (delete undocumented param) and PRM006 (reorder) overlap.

        Pass 1: PRM005 deletes ``c`` (not in signature).
        Pass 2: PRM006 reorders ``b, a`` → ``a, b``.
        """
        f = tmp_path / "example.py"
        src = (
            "def foo(a: int, b: str) -> bool:\n"
            '    """Do something.\n'
            "\n"
            "    Args:\n"
            "        c: Not in signature.\n"
            "        b: A string argument.\n"
            "        a: An integer argument.\n"
            "\n"
            '    """\n'
            "    return True\n"
        )
        f.write_text(src)
        diags, result, fixed = check_file(
            src,
            f,
            build_rules_map([PRM005(), PRM006()]),
            fix=True,
            unsafe_fixes=True,
        )
        assert result is not None
        # Both PRM005 and PRM006 should be fixed → fewer violations remaining than initially
        assert len(diags) - len(fixed) >= 2
        # ``c`` should be gone and ``a`` should come before ``b``
        assert "c: Not in signature" not in result
        a_pos = result.index("a: An integer argument")
        b_pos = result.index("b: A string argument")
        assert a_pos < b_pos

    def test_single_pass_sufficient(self, tmp_path: Path):
        """When fixes don't overlap, one pass is enough."""
        f = tmp_path / "example.py"
        src = (
            "def foo(a: int, b: str) -> bool:\n"
            '    """Do something.\n'
            "\n"
            "    Args:\n"
            "        b: A string argument.\n"
            "        a: An integer argument.\n"
            "\n"
            '    """\n'
            "    return True\n"
        )
        f.write_text(src)
        diags, result, fixed = check_file(
            src,
            f,
            build_rules_map([PRM006()]),
            fix=True,
            unsafe_fixes=True,
        )
        assert result is not None
        assert len(diags) - len(fixed) >= 1
        a_pos = result.index("a: An integer argument")
        b_pos = result.index("b: A string argument")
        assert a_pos < b_pos

    def test_no_infinite_loop(self, tmp_path: Path):
        """Ensure the loop converges even if fixes keep producing new diagnostics."""
        f = tmp_path / "example.py"
        # A simple case that should converge quickly
        src = (
            "def foo(a: int) -> bool:\n"
            '    """Do something.\n'
            "\n"
            "    Args:\n"
            "        x: Not in signature.\n"
            "\n"
            '    """\n'
            "    return True\n"
        )
        f.write_text(src)
        diags, result, fixed = check_file(
            src,
            f,
            build_rules_map([PRM005()]),
            fix=True,
            unsafe_fixes=True,
        )
        # Should converge and fix without hanging
        assert result is not None
        assert "x: Not in signature" not in result


class TestDOC001Integration:
    def test_fix_reorders_returns_before_args(self, tmp_path: Path):
        """DOC001 auto-fix puts Args before Returns in a multiline docstring."""
        f = tmp_path / "example.py"
        src = (
            "def add(a: int, b: int) -> int:\n"
            '    """Add two numbers.\n'
            "\n"
            "    Returns:\n"
            "        int: The sum.\n"
            "\n"
            "    Args:\n"
            "        a (int): First operand.\n"
            "        b (int): Second operand.\n"
            '    """\n'
            "    return a + b\n"
        )
        f.write_text(src)
        _, result, fixed = check_file(src, f, build_rules_map([DOC001()]), fix=True, unsafe_fixes=True)
        assert result is not None
        assert len(fixed) == 0  # all violations fixed, none remaining
        assert result.index("Args:") < result.index("Returns:")

    def test_prm001_rtn001_doc001_all_together(self, tmp_path: Path):
        """PRM001 + RTN001 insert sections; DOC001 then reorders them."""
        f = tmp_path / "example.py"
        src = 'def add(a: int, b: int) -> int:\n    """Add two numbers."""\n    return a + b\n'
        f.write_text(src)
        cfg = Config(skip_short_docstrings=False)
        _, result, _ = check_file(
            src,
            f,
            build_rules_map([PRM001(cfg), RTN001(cfg), DOC001()]),
            fix=True,
            unsafe_fixes=True,
        )
        assert result is not None
        # Regardless of insertion order, DOC001 should sort Args before Returns
        assert result.index("Args:") < result.index("Returns:")
