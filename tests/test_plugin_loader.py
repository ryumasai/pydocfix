"""Tests for plugin loader."""

from __future__ import annotations

import pytest

from pydocfix.rules._base import BaseRule
from pydocfix.rules.plugin_loader import (
    discover_rules_in_module,
    discover_rules_in_path,
    load_plugin_rules,
)


class TestDiscoverRulesInModule:
    """Tests for discover_rules_in_module()."""

    def test_discovers_from_known_module(self):
        """Discovers rules from a known built-in module."""
        rules = discover_rules_in_module("pydocfix.rules.sum.sum001")

        assert len(rules) >= 1
        assert all(issubclass(r, BaseRule) for r in rules)

    def test_raises_on_missing_module(self):
        """Raises ImportError for non-existent module."""
        with pytest.raises(ImportError):
            discover_rules_in_module("nonexistent.module.that.does.not.exist")


class TestDiscoverRulesInPath:
    """Tests for discover_rules_in_path()."""

    def test_discovers_rules_from_file(self, tmp_path):
        """Discovers rules from a Python file in a path."""
        rule_file = tmp_path / "custom_rules.py"
        rule_file.write_text("""\
from pydocfix.rules._base import BaseRule, DiagnoseContext, Diagnostic

class MY001(BaseRule):
    code = "MY001"
    enabled_by_default = True

    def diagnose(self, node, ctx):
        return iter([])
""")
        rules = discover_rules_in_path(tmp_path)

        assert any(r.code == "MY001" for r in rules)

    def test_empty_dir_returns_empty(self, tmp_path):
        """Empty directory returns empty list."""
        rules = discover_rules_in_path(tmp_path)

        assert rules == []


class TestLoadPluginRules:
    """Tests for load_plugin_rules()."""

    def test_empty_args_returns_empty(self):
        """No modules or paths returns empty list."""
        rules = load_plugin_rules(plugin_modules=[], plugin_paths=[])

        assert rules == []

    def test_loads_from_module(self):
        """Loads rules from a known module."""
        rules = load_plugin_rules(plugin_modules=["pydocfix.rules.sum.sum001"])

        assert len(rules) >= 1

    def test_loads_from_path(self, tmp_path):
        """Loads rules from a path directory."""
        rule_file = tmp_path / "my_rules.py"
        rule_file.write_text("""\
from pydocfix.rules._base import BaseRule, DiagnoseContext, Diagnostic

class MYRULE001(BaseRule):
    code = "MYRULE001"
    enabled_by_default = True

    def diagnose(self, node, ctx):
        return iter([])
""")
        rules = load_plugin_rules(plugin_paths=[tmp_path])

        assert any(r.code == "MYRULE001" for r in rules)

    def test_duplicate_code_uses_plugin_modules_order(self, tmp_path, monkeypatch):
        """Duplicate rule codes are resolved deterministically by module list order."""
        first = tmp_path / "plugin_first.py"
        second = tmp_path / "plugin_second.py"

        first.write_text("""\
from pydocfix.rules._base import BaseRule

class DUPFIRST(BaseRule):
    code = "DUP001"
    enabled_by_default = True

    def diagnose(self, node, ctx):
        return iter([])
""")
        second.write_text("""\
from pydocfix.rules._base import BaseRule

class DUPSECOND(BaseRule):
    code = "DUP001"
    enabled_by_default = True

    def diagnose(self, node, ctx):
        return iter([])
""")

        monkeypatch.syspath_prepend(str(tmp_path))

        rules = load_plugin_rules(plugin_modules=["plugin_second", "plugin_first"])
        dup_rules = [r for r in rules if r.code == "DUP001"]

        assert len(dup_rules) == 1
        assert dup_rules[0].__module__ == "plugin_second"
        assert dup_rules[0].__name__ == "DUPSECOND"
