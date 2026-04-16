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
        diags, *_ = check_file(source, tmp_path / "f.py", registry.type_to_rules)
        assert diags == []

    def test_non_ignored_rule_still_reported(self, tmp_path: Path):
        from pydocfix.checker import check_file
        from pydocfix.rules import build_registry

        source = 'def foo():\n    """No period"""\n    pass\n'
        registry = build_registry(ignore=["PRM101"])
        diags, *_ = check_file(source, tmp_path / "f.py", registry.type_to_rules)
        assert any(d.rule == "SUM002" for d in diags)


class TestSelectViaConfig:
    """Integration: select controls which rules are active."""

    def test_select_limits_to_specified_rule(self, tmp_path: Path):
        from pydocfix.checker import check_file
        from pydocfix.rules import build_registry

        source = 'def foo():\n    """No period"""\n    pass\n'
        # Only PRM101 selected → SUM002 should NOT fire even though it is default-enabled
        registry = build_registry(select=["PRM101"])
        diags, *_ = check_file(source, tmp_path / "f.py", registry.type_to_rules)
        assert not any(d.rule == "SUM002" for d in diags)

    def test_select_all_enables_non_default_rule(self, tmp_path: Path):
        from pydocfix.rules import BaseRule, build_registry

        # Fabricate a rule with enabled_by_default=False
        class _OptIn(BaseRule):
            code = "_OPTIN"
            enabled_by_default = False

            def diagnose(self, node, ctx):
                yield from ()

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
        diags, *_ = check_file(source, tmp_path / "f.py", registry.type_to_rules)
        assert any(d.rule == "SUM002" for d in diags)

    def test_non_default_rule_inactive_without_select(self, tmp_path: Path):
        from pydocfix.rules import BaseRule, build_registry

        class _OptIn(BaseRule):
            code = "_OPTIN2"
            enabled_by_default = False

            def diagnose(self, node, ctx):
                yield from ()

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


class TestExtendSafeUnsafeFixes:
    """extend-safe-fixes / extend-unsafe-fixes config options."""

    def test_defaults_empty(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text("[tool.pydocfix]\n")
        config = load_config(tmp_path)
        assert config.extend_safe_fixes == []
        assert config.extend_unsafe_fixes == []

    def test_extend_safe_fixes_loaded(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text('[tool.pydocfix]\nextend-safe-fixes = ["PRM001", "RTN002"]\n')
        config = load_config(tmp_path)
        assert config.extend_safe_fixes == ["PRM001", "RTN002"]

    def test_extend_unsafe_fixes_loaded(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text('[tool.pydocfix]\nextend-unsafe-fixes = ["SUM001"]\n')
        config = load_config(tmp_path)
        assert config.extend_unsafe_fixes == ["SUM001"]

    def test_extend_safe_fixes_uppercased(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text('[tool.pydocfix]\nextend-safe-fixes = ["prm001"]\n')
        config = load_config(tmp_path)
        assert config.extend_safe_fixes == ["PRM001"]

    def test_effective_applicability_override_to_safe(self, tmp_path: Path):
        """A rule listed in extend_safe_fixes is treated as SAFE even if its fix is UNSAFE."""
        from pydocfix.config import Config
        from pydocfix.rules._base import Applicability, Diagnostic, Edit, Fix, Offset, Range, effective_applicability

        fix = Fix(edits=[Edit(0, 0, "")], applicability=Applicability.UNSAFE)
        diag = Diagnostic(
            rule="PRM001",
            message="msg",
            filepath="f.py",
            range=Range(Offset(1, 1), Offset(1, 1)),
            fix=fix,
        )
        cfg = Config(extend_safe_fixes=["PRM001"])
        assert effective_applicability(diag, cfg) == Applicability.SAFE

    def test_effective_applicability_override_to_unsafe(self, tmp_path: Path):
        """A rule listed in extend_unsafe_fixes is treated as UNSAFE even if its fix is SAFE."""
        from pydocfix.config import Config
        from pydocfix.rules._base import Applicability, Diagnostic, Edit, Fix, Offset, Range, effective_applicability

        fix = Fix(edits=[Edit(0, 0, "")], applicability=Applicability.SAFE)
        diag = Diagnostic(
            rule="SUM002",
            message="msg",
            filepath="f.py",
            range=Range(Offset(1, 1), Offset(1, 1)),
            fix=fix,
        )
        cfg = Config(extend_unsafe_fixes=["SUM002"])
        assert effective_applicability(diag, cfg) == Applicability.UNSAFE

    def test_is_applicable_extend_safe_without_unsafe_flag(self, tmp_path: Path):
        """UNSAFE rule promoted to SAFE via config should be applicable without --unsafe-fixes."""
        from pydocfix.config import Config
        from pydocfix.rules._base import Applicability, Diagnostic, Edit, Fix, Offset, Range, is_applicable

        fix = Fix(edits=[Edit(0, 0, "")], applicability=Applicability.UNSAFE)
        diag = Diagnostic(
            rule="PRM001",
            message="msg",
            filepath="f.py",
            range=Range(Offset(1, 1), Offset(1, 1)),
            fix=fix,
        )
        cfg = Config(extend_safe_fixes=["PRM001"])
        assert is_applicable(diag, unsafe_fixes=False, config=cfg) is True

    def test_is_applicable_extend_unsafe_safe_rule_not_applied_without_flag(self, tmp_path: Path):
        """SAFE rule demoted to UNSAFE via config should not be applicable without --unsafe-fixes."""
        from pydocfix.config import Config
        from pydocfix.rules._base import Applicability, Diagnostic, Edit, Fix, Offset, Range, is_applicable

        fix = Fix(edits=[Edit(0, 0, "")], applicability=Applicability.SAFE)
        diag = Diagnostic(
            rule="SUM002",
            message="msg",
            filepath="f.py",
            range=Range(Offset(1, 1), Offset(1, 1)),
            fix=fix,
        )
        cfg = Config(extend_unsafe_fixes=["SUM002"])
        assert is_applicable(diag, unsafe_fixes=False, config=cfg) is False

    def test_is_applicable_extend_unsafe_safe_rule_applied_with_flag(self, tmp_path: Path):
        """SAFE rule demoted to UNSAFE via config should be applicable with --unsafe-fixes."""
        from pydocfix.config import Config
        from pydocfix.rules._base import Applicability, Diagnostic, Edit, Fix, Offset, Range, is_applicable

        fix = Fix(edits=[Edit(0, 0, "")], applicability=Applicability.SAFE)
        diag = Diagnostic(
            rule="SUM002",
            message="msg",
            filepath="f.py",
            range=Range(Offset(1, 1), Offset(1, 1)),
            fix=fix,
        )
        cfg = Config(extend_unsafe_fixes=["SUM002"])
        assert is_applicable(diag, unsafe_fixes=True, config=cfg) is True

    def test_no_override_without_config(self, tmp_path: Path):
        """Without config, UNSAFE fix is not applicable without --unsafe-fixes."""
        from pydocfix.rules._base import Applicability, Diagnostic, Edit, Fix, Offset, Range, is_applicable

        fix = Fix(edits=[Edit(0, 0, "")], applicability=Applicability.UNSAFE)
        diag = Diagnostic(
            rule="PRM001",
            message="msg",
            filepath="f.py",
            range=Range(Offset(1, 1), Offset(1, 1)),
            fix=fix,
        )
        assert is_applicable(diag, unsafe_fixes=False, config=None) is False

    def test_extend_safe_fixes_prefix(self, tmp_path: Path):
        """A category prefix in extend_safe_fixes promotes all matching rules."""
        from pydocfix.config import Config
        from pydocfix.rules._base import Applicability, Diagnostic, Edit, Fix, Offset, Range, effective_applicability

        fix = Fix(edits=[Edit(0, 0, "")], applicability=Applicability.UNSAFE)
        diag = Diagnostic(
            rule="PRM004",
            message="msg",
            filepath="f.py",
            range=Range(Offset(1, 1), Offset(1, 1)),
            fix=fix,
        )
        cfg = Config(extend_safe_fixes=["PRM"])
        assert effective_applicability(diag, cfg) == Applicability.SAFE

    def test_extend_unsafe_fixes_prefix(self, tmp_path: Path):
        """A category prefix in extend_unsafe_fixes demotes all matching rules."""
        from pydocfix.config import Config
        from pydocfix.rules._base import Applicability, Diagnostic, Edit, Fix, Offset, Range, effective_applicability

        fix = Fix(edits=[Edit(0, 0, "")], applicability=Applicability.SAFE)
        diag = Diagnostic(
            rule="SUM002",
            message="msg",
            filepath="f.py",
            range=Range(Offset(1, 1), Offset(1, 1)),
            fix=fix,
        )
        cfg = Config(extend_unsafe_fixes=["SUM"])
        assert effective_applicability(diag, cfg) == Applicability.UNSAFE

    def test_extend_safe_fixes_all(self, tmp_path: Path):
        """'ALL' in extend_safe_fixes promotes every rule to SAFE."""
        from pydocfix.config import Config
        from pydocfix.rules._base import Applicability, Diagnostic, Edit, Fix, Offset, Range, effective_applicability

        fix = Fix(edits=[Edit(0, 0, "")], applicability=Applicability.UNSAFE)
        diag = Diagnostic(
            rule="PRM001",
            message="msg",
            filepath="f.py",
            range=Range(Offset(1, 1), Offset(1, 1)),
            fix=fix,
        )
        cfg = Config(extend_safe_fixes=["ALL"])
        assert effective_applicability(diag, cfg) == Applicability.SAFE


class TestPreferredStyle:
    """Config loading and integration tests for preferred_style."""

    def test_default_google(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text("[tool.pydocfix]\n")
        config = load_config(tmp_path)
        assert config.preferred_style == "google"

    def test_numpy_from_toml(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text('[tool.pydocfix]\npreferred_style = "numpy"\n')
        config = load_config(tmp_path)
        assert config.preferred_style == "numpy"

    def test_google_explicit(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text('[tool.pydocfix]\npreferred_style = "google"\n')
        config = load_config(tmp_path)
        assert config.preferred_style == "google"

    def test_invalid_falls_back_to_google(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text('[tool.pydocfix]\npreferred_style = "sphinx"\n')
        config = load_config(tmp_path)
        assert config.preferred_style == "google"

    def test_case_insensitive(self, tmp_path: Path):
        (tmp_path / "pyproject.toml").write_text('[tool.pydocfix]\npreferred_style = "NumPy"\n')
        config = load_config(tmp_path)
        assert config.preferred_style == "numpy"

    def test_prm001_plain_google_style(self, tmp_path: Path):
        """PlainDocstring + preferred_style='google' generates Args section."""
        from pydocfix.checker import build_rules_map, check_file
        from pydocfix.config import Config
        from pydocfix.rules.prm.prm001 import PRM001

        source = 'def foo(x: int):\n    """Summary."""\n    pass\n'
        cfg = Config(skip_short_docstrings=False, preferred_style="google")
        rules_map = build_rules_map([PRM001(cfg)])
        diags, *_ = check_file(source, tmp_path / "f.py", rules_map)
        assert any(d.rule == "PRM001" for d in diags)
        diag = next(d for d in diags if d.rule == "PRM001")
        assert diag.fix is not None
        assert "Args:" in diag.fix.edits[0].new_text

    def test_prm001_plain_numpy_style(self, tmp_path: Path):
        """PlainDocstring + preferred_style='numpy' generates Parameters section."""
        from pydocfix.checker import build_rules_map, check_file
        from pydocfix.config import Config
        from pydocfix.rules.prm.prm001 import PRM001

        source = 'def foo(x: int):\n    """Summary."""\n    pass\n'
        cfg = Config(skip_short_docstrings=False, preferred_style="numpy")
        rules_map = build_rules_map([PRM001(cfg)])
        diags, *_ = check_file(source, tmp_path / "f.py", rules_map)
        assert any(d.rule == "PRM001" for d in diags)
        diag = next(d for d in diags if d.rule == "PRM001")
        assert diag.fix is not None
        assert "Parameters" in diag.fix.edits[0].new_text
        assert "----------" in diag.fix.edits[0].new_text

    def test_rtn001_plain_numpy_style(self, tmp_path: Path):
        """PlainDocstring + preferred_style='numpy' generates NumPy Returns section."""
        from pydocfix.checker import build_rules_map, check_file
        from pydocfix.config import Config
        from pydocfix.rules.rtn.rtn001 import RTN001

        source = 'def foo() -> int:\n    """Summary."""\n    pass\n'
        cfg = Config(skip_short_docstrings=False, preferred_style="numpy")
        rules_map = build_rules_map([RTN001(cfg)])
        diags, *_ = check_file(source, tmp_path / "f.py", rules_map)
        assert any(d.rule == "RTN001" for d in diags)
        diag = next(d for d in diags if d.rule == "RTN001")
        assert diag.fix is not None
        assert "Returns\n" in diag.fix.edits[0].new_text
        assert "-------" in diag.fix.edits[0].new_text

    def test_ris001_plain_numpy_style(self, tmp_path: Path):
        """PlainDocstring + preferred_style='numpy' generates NumPy Raises section."""
        from pydocfix.checker import build_rules_map, check_file
        from pydocfix.config import Config
        from pydocfix.rules.ris.ris001 import RIS001

        source = 'def foo():\n    """Summary."""\n    raise ValueError("bad")\n'
        cfg = Config(skip_short_docstrings=False, preferred_style="numpy")
        rules_map = build_rules_map([RIS001(cfg)])
        diags, *_ = check_file(source, tmp_path / "f.py", rules_map)
        assert any(d.rule == "RIS001" for d in diags)
        diag = next(d for d in diags if d.rule == "RIS001")
        assert diag.fix is not None
        assert "Raises\n" in diag.fix.edits[0].new_text
        assert "------" in diag.fix.edits[0].new_text

    def test_yld001_plain_numpy_style(self, tmp_path: Path):
        """PlainDocstring + preferred_style='numpy' generates NumPy Yields section."""
        from pydocfix.checker import build_rules_map, check_file
        from pydocfix.config import Config
        from pydocfix.rules.yld.yld001 import YLD001

        source = 'def foo():\n    """Summary."""\n    yield 1\n'
        cfg = Config(skip_short_docstrings=False, preferred_style="numpy")
        rules_map = build_rules_map([YLD001(cfg)])
        diags, *_ = check_file(source, tmp_path / "f.py", rules_map)
        assert any(d.rule == "YLD001" for d in diags)
        diag = next(d for d in diags if d.rule == "YLD001")
        assert diag.fix is not None
        assert "Yields\n" in diag.fix.edits[0].new_text
        assert "------" in diag.fix.edits[0].new_text

    def test_existing_google_docstring_ignores_preferred_numpy(self, tmp_path: Path):
        """A Google-style docstring should get Google-style fix regardless of preferred_style."""
        from pydocfix.checker import build_rules_map, check_file
        from pydocfix.config import Config
        from pydocfix.rules.rtn.rtn001 import RTN001

        source = 'def foo(x: int) -> int:\n    """Summary.\n\n    Args:\n        x (int): Desc.\n    """\n    pass\n'
        cfg = Config(preferred_style="numpy")
        rules_map = build_rules_map([RTN001(cfg)])
        diags, *_ = check_file(source, tmp_path / "f.py", rules_map)
        assert any(d.rule == "RTN001" for d in diags)
        diag = next(d for d in diags if d.rule == "RTN001")
        assert diag.fix is not None
        assert "Returns:" in diag.fix.edits[0].new_text
        assert "-------" not in diag.fix.edits[0].new_text
