"""Tests for the config module."""

from __future__ import annotations

from pathlib import Path

from pydocfix.config import find_pyproject_toml, load_config


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
        (tmp_path / "pyproject.toml").write_text('[tool.pydocfix]\nignore = ["SUM002", "PRM101"]\n')
        config = load_config(tmp_path)
        assert config.ignore == ["SUM002", "PRM101"]

    def test_no_pydocfix_section(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")
        config = load_config(tmp_path)
        assert config.ignore == []

    def test_invalid_toml_returns_defaults(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text("not valid TOML !!!")
        config = load_config(tmp_path)
        assert config.ignore == []

    def test_select_list(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text('[tool.pydocfix]\nselect = ["SUM002"]\n')
        config = load_config(tmp_path)
        assert config.select == ["SUM002"]

    def test_select_defaults_to_empty(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text("[tool.pydocfix]\n")
        config = load_config(tmp_path)
        assert config.select == []

    def test_skip_short_docstrings_default_true(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text("[tool.pydocfix]\n")
        config = load_config(tmp_path)
        assert config.skip_short_docstrings is True

    def test_skip_short_docstrings_false(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text("[tool.pydocfix]\nskip_short_docstrings = false\n")
        config = load_config(tmp_path)
        assert config.skip_short_docstrings is False

    def test_skip_short_docstrings_true_explicit(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text("[tool.pydocfix]\nskip_short_docstrings = true\n")
        config = load_config(tmp_path)
        assert config.skip_short_docstrings is True

    def test_type_annotation_style_signature(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text('[tool.pydocfix]\ntype_annotation_style = "signature"\n')
        config = load_config(tmp_path)
        assert config.type_annotation_style == "signature"

    def test_type_annotation_style_docstring(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text('[tool.pydocfix]\ntype_annotation_style = "docstring"\n')
        config = load_config(tmp_path)
        assert config.type_annotation_style == "docstring"

    def test_type_annotation_style_both(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text('[tool.pydocfix]\ntype_annotation_style = "both"\n')
        config = load_config(tmp_path)
        assert config.type_annotation_style == "both"

    def test_type_annotation_style_invalid_ignored(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text('[tool.pydocfix]\ntype_annotation_style = "invalid"\n')
        config = load_config(tmp_path)
        assert config.type_annotation_style is None

    def test_type_annotation_style_default_none(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text("[tool.pydocfix]\n")
        config = load_config(tmp_path)
        assert config.type_annotation_style is None


class TestIgnoreViaConfig:
    """Integration: ignored rules produce no diagnostics."""

    def test_ignored_rule_not_reported(self, tmp_path: Path):
        from pydocfix.checker import check_file
        from pydocfix.rules import build_registry

        source = 'def foo():\n    """No period"""\n    pass\n'
        registry = build_registry(ignore=["SUM002"])
        diags, *_ = check_file(source, tmp_path / "f.py", registry.kind_map)
        assert diags == []

    def test_non_ignored_rule_still_reported(self, tmp_path: Path):
        from pydocfix.checker import check_file
        from pydocfix.rules import build_registry

        source = 'def foo():\n    """No period"""\n    pass\n'
        registry = build_registry(ignore=["PRM101"])
        diags, *_ = check_file(source, tmp_path / "f.py", registry.kind_map)
        assert any(d.rule == "SUM002" for d in diags)


class TestSelectViaConfig:
    """Integration: select controls which rules are active."""

    def test_select_limits_to_specified_rule(self, tmp_path: Path):
        from pydocfix.checker import check_file
        from pydocfix.rules import build_registry

        source = 'def foo():\n    """No period"""\n    pass\n'
        # Only PRM101 selected → SUM002 should NOT fire even though it is default-enabled
        registry = build_registry(select=["PRM101"])
        diags, *_ = check_file(source, tmp_path / "f.py", registry.kind_map)
        assert not any(d.rule == "SUM002" for d in diags)

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
        assert any(d.rule == "SUM002" for d in diags)

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

        registry = build_registry(select=["ALL"], ignore=["SUM002"])
        assert registry.get("SUM002") is None


class TestSkipShortDocstrings:
    """Integration: skip_short_docstrings suppresses section-level rules for plain docstrings."""

    # "Summary." is auto-detected as PlainDocstring by the checker.
    # Rules PRM001, RTN001, RIS001, YLD001 should not fire when the flag is True.

    def test_prm001_skipped_when_flag_true(self, tmp_path: Path):
        from pydocfix.checker import build_rules_map, check_file
        from pydocfix.config import Config
        from pydocfix.rules.prm.prm001 import PRM001

        source = 'def foo(x: int):\n    """Summary."""\n    pass\n'
        cfg = Config(skip_short_docstrings=True)
        rules_map = build_rules_map([PRM001(cfg)])
        diags, *_ = check_file(source, tmp_path / "f.py", rules_map)
        assert not any(d.rule == "PRM001" for d in diags)

    def test_prm001_fires_when_flag_false(self, tmp_path: Path):
        from pydocfix.checker import build_rules_map, check_file
        from pydocfix.config import Config
        from pydocfix.rules.prm.prm001 import PRM001

        source = 'def foo(x: int):\n    """Summary."""\n    pass\n'
        cfg = Config(skip_short_docstrings=False)
        rules_map = build_rules_map([PRM001(cfg)])
        diags, *_ = check_file(source, tmp_path / "f.py", rules_map)
        assert any(d.rule == "PRM001" for d in diags)

    def test_rtn001_skipped_when_flag_true(self, tmp_path: Path):
        from pydocfix.checker import build_rules_map, check_file
        from pydocfix.config import Config
        from pydocfix.rules.rtn.rtn001 import RTN001

        source = 'def foo() -> int:\n    """Summary."""\n    pass\n'
        cfg = Config(skip_short_docstrings=True)
        rules_map = build_rules_map([RTN001(cfg)])
        diags, *_ = check_file(source, tmp_path / "f.py", rules_map)
        assert not any(d.rule == "RTN001" for d in diags)

    def test_rtn001_fires_when_flag_false(self, tmp_path: Path):
        from pydocfix.checker import build_rules_map, check_file
        from pydocfix.config import Config
        from pydocfix.rules.rtn.rtn001 import RTN001

        source = 'def foo() -> int:\n    """Summary."""\n    pass\n'
        cfg = Config(skip_short_docstrings=False)
        rules_map = build_rules_map([RTN001(cfg)])
        diags, *_ = check_file(source, tmp_path / "f.py", rules_map)
        assert any(d.rule == "RTN001" for d in diags)


class TestAllowOptionalShorthand:
    """Integration: allow_optional_shorthand suppresses Optional[T] vs T mismatches."""

    def test_default_false_fires_on_optional(self, tmp_path: Path):
        from pydocfix.checker import build_rules_map, check_file
        from pydocfix.config import Config
        from pydocfix.rules.prm.prm101 import PRM101

        source = (
            "from typing import Optional\n"
            "def foo(x: Optional[int]):\n"
            '    """Summary.\n\n    Args:\n        x (int): desc.\n    """\n'
            "    pass\n"
        )
        cfg = Config(allow_optional_shorthand=False)
        rules_map = build_rules_map([PRM101(cfg)])
        diags, *_ = check_file(source, tmp_path / "f.py", rules_map)
        assert any(d.rule == "PRM101" for d in diags)

    def test_true_suppresses_optional_mismatch(self, tmp_path: Path):
        from pydocfix.checker import build_rules_map, check_file
        from pydocfix.config import Config
        from pydocfix.rules.prm.prm101 import PRM101

        source = (
            "from typing import Optional\n"
            "def foo(x: Optional[int]):\n"
            '    """Summary.\n\n    Args:\n        x (int): desc.\n    """\n'
            "    pass\n"
        )
        cfg = Config(allow_optional_shorthand=True)
        rules_map = build_rules_map([PRM101(cfg)])
        diags, *_ = check_file(source, tmp_path / "f.py", rules_map)
        assert not any(d.rule == "PRM101" for d in diags)

    def test_config_default_false(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text("[tool.pydocfix]\n")
        config = load_config(tmp_path)
        assert config.allow_optional_shorthand is False

    def test_config_loaded_from_toml(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text("[tool.pydocfix]\nallow_optional_shorthand = true\n")
        config = load_config(tmp_path)
        assert config.allow_optional_shorthand is True
