"""Tests for plugin discovery and loading — H-1 to H-6."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest
from pydocstring import PlainDocstring

from pydocfix.plugin_loader import discover_rules_in_module, discover_rules_in_path, load_plugin_rules
from pydocfix.rules import build_registry
from pydocfix.rules._base import BaseRule, DiagnoseContext

_PLUGINS = Path(__file__).parent / "_plugins"
_DISCOVERY_DIR = _PLUGINS / "discovery"
_CONFLICT_MOD_PARENT = _PLUGINS  # add to sys.path so "conflict_mod" is importable
_CONFLICT_PATH_DIR = _PLUGINS / "conflict_path"


# Duplicate of a built-in code — used for H-6
class _DupSUM001(BaseRule[PlainDocstring]):
    """Duplicate SUM001 for testing builtin-wins-over-plugin precedence."""

    code = "SUM001"

    def diagnose(self, node, ctx: DiagnoseContext):
        return iter(())


class TestDiscoverRulesInModule:
    """H-1, H-2: discover_rules_in_module()."""

    def test_discovers_rules_from_known_module(self):
        """H-1: known built-in module yields its rule class."""
        rules = discover_rules_in_module("pydocfix.rules.sum.sum001")

        assert len(rules) == 1
        assert rules[0].code == "SUM001"

    def test_raises_on_missing_module(self):
        """H-2: non-existent module raises ImportError."""
        with pytest.raises(ImportError):
            discover_rules_in_module("nonexistent.module.xyz")


class TestDiscoverRulesInPath:
    """H-3, H-4: discover_rules_in_path()."""

    def test_discovers_rules_from_directory(self):
        """H-3: plugin001.py in discovery/ is discovered."""
        rules = discover_rules_in_path(_DISCOVERY_DIR)

        assert any(r.code == "PLUGIN001" for r in rules)

    def test_skips_underscore_prefixed_files(self):
        """H-4: _plugin002.py is skipped even though it defines a valid rule."""
        rules = discover_rules_in_path(_DISCOVERY_DIR)

        assert not any(r.code == "PLUGIN002" for r in rules)


class TestLoadPluginRules:
    """H-5: load_plugin_rules() precedence."""

    def test_plugin_modules_take_precedence_over_plugin_paths(self, monkeypatch):
        """H-5: when the same code appears in modules and paths, modules wins."""
        monkeypatch.syspath_prepend(str(_CONFLICT_MOD_PARENT))

        rules = load_plugin_rules(
            plugin_modules=["conflict_mod.plugin003"],
            plugin_paths=[_CONFLICT_PATH_DIR],
        )

        plugin003_rules = [r for r in rules if r.code == "PLUGIN003"]
        assert len(plugin003_rules) == 1
        assert plugin003_rules[0].__module__ == "conflict_mod.plugin003"


class TestBuildRegistryPluginPrecedence:
    """H-6: build_registry() resolves conflicts between built-ins and plugins."""

    def test_builtin_wins_over_plugin_with_same_code(self, caplog):
        """H-6: built-in rule is kept when a plugin reuses its code; warning logged."""
        with caplog.at_level(logging.WARNING):
            registry = build_registry(select=["SUM001"], plugin_rules=[_DupSUM001])

        rule = registry.get("SUM001")
        assert rule is not None
        assert rule.__class__.__module__ == "pydocfix.rules.sum.sum001"
        assert any("SUM001" in r.message and r.levelno == logging.WARNING for r in caplog.records)
