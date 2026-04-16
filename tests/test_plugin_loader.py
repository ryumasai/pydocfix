"""Tests for plugin loader."""

from __future__ import annotations

import tempfile
from pathlib import Path
from textwrap import dedent

import pytest

from pydocfix.rules._base import BaseRule
from pydocfix.rules.plugin_loader import (
    discover_rules_in_module,
    discover_rules_in_package,
    discover_rules_in_path,
    load_plugin_rules,
)


def test_discover_rules_in_module_builtin():
    """Test discovering rules from a built-in module."""
    rules = discover_rules_in_module("pydocfix.rules.sum")
    assert len(rules) >= 2
    codes = {r.code for r in rules}
    assert "SUM001" in codes
    assert "SUM002" in codes


def test_discover_rules_in_package_builtin():
    """Test discovering rules from a built-in package."""
    rules = discover_rules_in_package("pydocfix.rules.prm")
    assert len(rules) >= 10
    codes = {r.code for r in rules}
    assert "PRM001" in codes
    assert "PRM101" in codes


def test_discover_rules_in_path():
    """Test discovering rules from a file system path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create a simple custom rule
        custom_rule = tmppath / "my_custom_rule.py"
        custom_rule.write_text(
            dedent("""
            from pydocfix.rules._base import BaseRule, DiagnoseContext, Diagnostic
            from pydocstring import GoogleDocstring
            from collections.abc import Iterator

            class CUSTOM001(BaseRule[GoogleDocstring]):
                code = "CUSTOM001"
                enabled_by_default = True

                def diagnose(self, node, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
                    yield self._make_diagnostic(
                        ctx,
                        "Custom rule triggered",
                        target=node,
                    )
        """)
        )

        rules = discover_rules_in_path(tmppath)
        assert len(rules) == 1
        assert rules[0].code == "CUSTOM001"


def test_load_plugin_rules_from_module():
    """Test loading plugin rules from a module name."""
    rules = load_plugin_rules(plugin_modules=["pydocfix.rules.sum"])
    assert len(rules) >= 2
    codes = {r.code for r in rules}
    assert "SUM001" in codes


def test_load_plugin_rules_from_path():
    """Test loading plugin rules from a file path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create a custom rule
        custom_rule = tmppath / "test_rule.py"
        custom_rule.write_text(
            dedent("""
            from pydocfix.rules._base import BaseRule, DiagnoseContext, Diagnostic
            from pydocstring import GoogleDocstring
            from collections.abc import Iterator

            class TEST001(BaseRule[GoogleDocstring]):
                code = "TEST001"

                def diagnose(self, node, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
                    return
                    yield  # unreachable
        """)
        )

        rules = load_plugin_rules(plugin_paths=[tmppath])
        assert len(rules) == 1
        assert rules[0].code == "TEST001"


def test_load_plugin_rules_skip_abstract():
    """Test that abstract classes with missing code raise errors during import."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create an abstract rule (missing code)
        abstract_rule = tmppath / "abstract_rule.py"
        abstract_rule.write_text(
            dedent("""
            from pydocfix.rules._base import BaseRule

            class AbstractRule(BaseRule):
                pass  # No code attribute - this will raise TypeError
        """)
        )

        # discover_rules_in_path should handle the import error gracefully
        # and return empty list
        rules = discover_rules_in_path(tmppath)
        assert len(rules) == 0


def test_load_plugin_rules_duplicate_codes():
    """Test that duplicate codes are warned about."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create two rules with the same code
        rule1 = tmppath / "rule1.py"
        rule1.write_text(
            dedent("""
            from pydocfix.rules._base import BaseRule, DiagnoseContext, Diagnostic
            from pydocstring import GoogleDocstring
            from collections.abc import Iterator

            class DUP001_First(BaseRule[GoogleDocstring]):
                code = "DUP001"

                def diagnose(self, node, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
                    return
                    yield
        """)
        )

        rule2 = tmppath / "rule2.py"
        rule2.write_text(
            dedent("""
            from pydocfix.rules._base import BaseRule, DiagnoseContext, Diagnostic
            from pydocstring import GoogleDocstring
            from collections.abc import Iterator

            class DUP001_Second(BaseRule[GoogleDocstring]):
                code = "DUP001"

                def diagnose(self, node, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
                    return
                    yield
        """)
        )

        # Should still load both but warn
        rules = discover_rules_in_path(tmppath)
        assert len(rules) == 2
        assert all(r.code == "DUP001" for r in rules)


def test_discover_rules_invalid_module():
    """Test that invalid modules are handled gracefully."""
    with pytest.raises(ImportError):
        discover_rules_in_module("nonexistent.module.path")


def test_discover_rules_in_path_nonexistent():
    """Test that nonexistent paths are handled gracefully."""
    rules = discover_rules_in_path(Path("/nonexistent/path"))
    assert rules == []
