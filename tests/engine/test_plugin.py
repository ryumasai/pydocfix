"""Tests for plugin discovery and loading."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path

import pytest
from pydocstring import PlainDocstring

from pydocfix.diagnostics import Diagnostic
from pydocfix.engine.plugin_loader import discover_rules_in_module, discover_rules_in_path, load_plugin_rules
from pydocfix.rules import build_registry
from pydocfix.rules._base import BaseCtx, FunctionCtx, ModuleCtx, make_diagnostic, rule

_PLUGINS = Path(__file__).parent / "_plugins"
_DISCOVERY_DIR = _PLUGINS / "discovery"
_CONFLICT_MOD_PARENT = _PLUGINS  # add to sys.path so "conflict_mod" is importable
_CONFLICT_PATH_DIR = _PLUGINS / "conflict_path"


# Duplicate of a built-in code
@rule("SUM001", ctx_types=frozenset({FunctionCtx, ModuleCtx}), cst_types=frozenset({PlainDocstring}))
def _dup_sum001(node: PlainDocstring, ctx: BaseCtx) -> Iterator[Diagnostic]:
    """Duplicate SUM001 for testing builtin-wins-over-plugin precedence."""
    return iter(())


class TestDiscoverRulesInModule:
    """discover_rules_in_module()."""

    def test_discovers_rules_from_known_module(self):
        """known built-in module yields its rule function."""
        rules = discover_rules_in_module("pydocfix.rules.sum.sum001")

        assert len(rules) == 1
        assert rules[0]._rule_code == "SUM001"

    def test_raises_on_missing_module(self):
        """non-existent module raises ImportError."""
        with pytest.raises(ImportError):
            discover_rules_in_module("nonexistent.module.xyz")

    def test_module_with_no_rules_returns_empty(self):
        """a valid module that defines no @rule functions returns []."""
        rules = discover_rules_in_module("pydocfix.diagnostics")

        assert rules == []


class TestDiscoverRulesInPath:
    """discover_rules_in_path()."""

    def test_discovers_rules_from_directory(self):
        """plugin001.py in discovery/ is discovered."""
        rules = discover_rules_in_path(_DISCOVERY_DIR)

        assert any(r._rule_code == "PLUGIN001" for r in rules)

    def test_skips_underscore_prefixed_files(self):
        """_plugin002.py is skipped even though it defines a valid rule."""
        rules = discover_rules_in_path(_DISCOVERY_DIR)

        assert not any(r._rule_code == "PLUGIN002" for r in rules)

    def test_nonexistent_path_returns_empty(self, tmp_path):
        """non-existent path returns an empty list."""
        rules = discover_rules_in_path(tmp_path / "does_not_exist")

        assert rules == []

    def test_file_path_returns_empty(self, tmp_path):
        """passing a file (not a directory) returns an empty list."""
        f = tmp_path / "not_a_dir.py"
        f.touch()
        rules = discover_rules_in_path(f)

        assert rules == []


class TestLoadPluginRules:
    """load_plugin_rules() precedence."""

    def test_plugin_modules_take_precedence_over_plugin_paths(self, monkeypatch):
        """when the same code appears in modules and paths, modules wins."""
        monkeypatch.syspath_prepend(str(_CONFLICT_MOD_PARENT))

        rules = load_plugin_rules(
            plugin_modules=["conflict_mod.plugin003"],
            plugin_paths=[_CONFLICT_PATH_DIR],
        )

        plugin003_rules = [r for r in rules if r._rule_code == "PLUGIN003"]
        assert len(plugin003_rules) == 1
        assert plugin003_rules[0].__module__ == "conflict_mod.plugin003"


class TestBuildRegistryPluginPrecedence:
    """build_registry() resolves conflicts between built-ins and plugins."""

    def test_builtin_wins_over_plugin_with_same_code(self, caplog):
        """built-in rule is kept when a plugin reuses its code; warning logged."""
        with caplog.at_level(logging.WARNING):
            registry = build_registry(select=["SUM001"], plugin_rules=[_dup_sum001])

        rule_fn = registry.get("SUM001")
        assert rule_fn is not None
        assert rule_fn.__module__ == "pydocfix.rules.sum.sum001"
        assert any("SUM001" in r.message and r.levelno == logging.WARNING for r in caplog.records)
