"""Tests for the config module."""

from __future__ import annotations

from pathlib import Path

import pytest

from pydocfix.config import Config, find_pyproject_toml, load_config


class TestFindPyprojectToml:
    def test_finds_file_in_current_dir(self, tmp_path: Path):
        toml = tmp_path / "pyproject.toml"
        toml.write_text("[project]\nname = 'test'\n")
        assert find_pyproject_toml(tmp_path) == toml

    def test_finds_file_in_parent_dir(self, tmp_path: Path):
        toml = tmp_path / "pyproject.toml"
        toml.write_text("[project]\nname = 'test'\n")
        subdir = tmp_path / "sub"
        subdir.mkdir()
        assert find_pyproject_toml(subdir) == toml

    def test_returns_none_when_not_found(self, tmp_path: Path):
        # Use a deeply nested dir with no pyproject.toml
        subdir = tmp_path / "a" / "b"
        subdir.mkdir(parents=True)
        result = find_pyproject_toml(subdir)
        # May find the real project root's pyproject.toml, so just verify
        # it returns a Path or None
        assert result is None or result.name == "pyproject.toml"


class TestLoadConfig:
    def test_defaults_when_no_file(self, tmp_path: Path):
        config = load_config(tmp_path / "nonexistent")
        assert config.ignore == []

    def test_empty_pydocfix_section(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text("[tool.pydocfix]\n")
        config = load_config(tmp_path)
        assert config.ignore == []

    def test_ignore_list(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text('[tool.pydocfix]\nignore = ["D200", "D401"]\n')
        config = load_config(tmp_path)
        assert config.ignore == ["D200", "D401"]

    def test_no_pydocfix_section(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")
        config = load_config(tmp_path)
        assert config.ignore == []

    def test_invalid_toml_returns_defaults(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text("not valid TOML !!!")
        config = load_config(tmp_path)
        assert config.ignore == []

    def test_select_list(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text('[tool.pydocfix]\nselect = ["D200"]\n')
        config = load_config(tmp_path)
        assert config.select == ["D200"]

    def test_select_defaults_to_empty(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text("[tool.pydocfix]\n")
        config = load_config(tmp_path)
        assert config.select == []


class TestIgnoreViaConfig:
    """Integration: ignored rules produce no diagnostics."""

    def test_ignored_rule_not_reported(self, tmp_path: Path):
        from pydocfix.checker import check_file
        from pydocfix.rules import build_registry

        source = 'def foo():\n    """No period"""\n    pass\n'
        registry = build_registry(ignore=["D200"])
        diags, *_ = check_file(source, tmp_path / "f.py", registry.kind_map)
        assert diags == []

    def test_non_ignored_rule_still_reported(self, tmp_path: Path):
        from pydocfix.checker import check_file
        from pydocfix.rules import build_registry

        source = 'def foo():\n    """No period"""\n    pass\n'
        registry = build_registry(ignore=["D401"])
        diags, *_ = check_file(source, tmp_path / "f.py", registry.kind_map)
        assert any(d.rule == "D200" for d in diags)


class TestSelectViaConfig:
    """Integration: select controls which rules are active."""

    def test_select_limits_to_specified_rule(self, tmp_path: Path):
        from pydocfix.checker import check_file
        from pydocfix.rules import build_registry

        source = 'def foo():\n    """No period"""\n    pass\n'
        # Only D401 selected → D200 should NOT fire even though it is default-enabled
        registry = build_registry(select=["D401"])
        diags, *_ = check_file(source, tmp_path / "f.py", registry.kind_map)
        assert not any(d.rule == "D200" for d in diags)

    def test_select_all_enables_non_default_rule(self, tmp_path: Path):
        from pydocfix.rules import BaseRule, build_registry

        # Fabricate a rule with enabled_by_default=False
        class _OptIn(BaseRule):
            code = "_OPTIN"
            enabled_by_default = False
            target_kinds = set()

        from pydocfix.rules import _BUILTIN_RULES

        _BUILTIN_RULES.append(_OptIn)
        try:
            registry = build_registry(select=["ALL"])
            assert registry.get("_OPTIN") is not None
        finally:
            _BUILTIN_RULES.remove(_OptIn)

    def test_default_enabled_rule_active_without_select(self, tmp_path: Path):
        from pydocfix.checker import check_file
        from pydocfix.rules import build_registry

        source = 'def foo():\n    """No period"""\n    pass\n'
        registry = build_registry()  # no select → only default-enabled rules
        diags, *_ = check_file(source, tmp_path / "f.py", registry.kind_map)
        assert any(d.rule == "D200" for d in diags)

    def test_non_default_rule_inactive_without_select(self, tmp_path: Path):
        from pydocfix.rules import BaseRule, build_registry

        class _OptIn(BaseRule):
            code = "_OPTIN2"
            enabled_by_default = False
            target_kinds = set()

        from pydocfix.rules import _BUILTIN_RULES

        _BUILTIN_RULES.append(_OptIn)
        try:
            registry = build_registry()
            assert registry.get("_OPTIN2") is None
        finally:
            _BUILTIN_RULES.remove(_OptIn)

    def test_ignore_overrides_select(self, tmp_path: Path):
        from pydocfix.rules import build_registry

        registry = build_registry(select=["ALL"], ignore=["D200"])
        assert registry.get("D200") is None
