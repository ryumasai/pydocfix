"""Tests for checker integration — G-1 to G-13."""

from __future__ import annotations

from pathlib import Path

from pydocfix.checker import check_file
from pydocfix.config import Config
from tests.engine._rules.always001 import ALWAYS001
from tests.engine._rules.safe001 import SAFE001
from tests.engine._rules.unsafe001 import UNSAFE001
from tests.helpers import make_registry

_PATH = Path("test.py")


def _registry(*rules):
    """Build a type_to_rules map from rule instances."""
    return make_registry(*rules).type_to_rules


class TestCheckFileBasic:
    """G-1 to G-5: basic detection and syntax error handling."""

    def test_detects_violation(self, load_fixture):
        """G-1: violation in docstring produces a diagnostic."""
        source = load_fixture("safe_violation.py")
        diagnostics, _, _ = check_file(source, _PATH, _registry(SAFE001(Config())))

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "SAFE001"

    def test_no_violation_returns_empty(self, load_fixture):
        """G-2: clean docstring produces no diagnostics."""
        source = load_fixture("no_violation.py")
        diagnostics, _, _ = check_file(source, _PATH, _registry(SAFE001(Config())))

        assert diagnostics == []

    def test_detects_all_violations_in_file(self, load_fixture):
        """G-3: every violating docstring in a file is diagnosed."""
        source = load_fixture("two_violations.py")
        diagnostics, _, _ = check_file(source, _PATH, _registry(SAFE001(Config())))

        assert len(diagnostics) == 2
        assert all(d.rule == "SAFE001" for d in diagnostics)

    def test_syntax_error_returns_empty(self):
        """G-4: source with a syntax error returns empty diagnostics and no fix."""
        source = "def broken(\n"
        diagnostics, fixed, _ = check_file(source, _PATH, _registry(SAFE001(Config())))

        assert diagnostics == []
        assert fixed is None


class TestCheckFileFix:
    """G-5 to G-8: fix application modes."""

    def test_no_fix_without_flag(self, load_fixture):
        """G-5: fix=False returns fixed_source=None."""
        source = load_fixture("safe_violation.py")
        _, fixed, _ = check_file(source, _PATH, _registry(SAFE001(Config())), fix=False)

        assert fixed is None

    def test_safe_fix_applied(self, load_fixture):
        """G-6: SAFE fix is applied when fix=True."""
        source = load_fixture("safe_violation.py")
        _, fixed, _ = check_file(source, _PATH, _registry(SAFE001(Config())), fix=True)

        assert fixed is not None
        assert "FIXED(SAFE001)" in fixed

    def test_unsafe_fix_not_applied_without_flag(self, load_fixture):
        """G-7: UNSAFE fix is not applied when unsafe_fixes=False."""
        source = load_fixture("unsafe_violation.py")
        _, fixed, _ = check_file(source, _PATH, _registry(UNSAFE001(Config())), fix=True, unsafe_fixes=False)

        assert fixed is None

    def test_unsafe_fix_applied_with_flag(self, load_fixture):
        """G-8: UNSAFE fix is applied when unsafe_fixes=True."""
        source = load_fixture("unsafe_violation.py")
        _, fixed, _ = check_file(source, _PATH, _registry(UNSAFE001(Config())), fix=True, unsafe_fixes=True)

        assert fixed is not None
        assert "FIXED(UNSAFE001)" in fixed


class TestCheckFileNoqa:
    """G-9 to G-12: noqa suppression behaviour."""

    def test_blanket_noqa_suppresses_all(self, load_fixture):
        """G-9: # noqa (blanket) suppresses every rule."""
        source = load_fixture("blanket_noqa.py")
        diagnostics, _, _ = check_file(source, _PATH, _registry(ALWAYS001(Config())))

        assert not any(d.rule == "ALWAYS001" for d in diagnostics)

    def test_specific_noqa_suppresses_only_listed_code(self, load_fixture):
        """G-10: # noqa: SAFE001 suppresses SAFE001 but leaves ALWAYS001 active."""
        source = load_fixture("specific_noqa.py")
        rules = _registry(SAFE001(Config()), ALWAYS001(Config()))
        diagnostics, _, _ = check_file(source, _PATH, rules)

        codes = {d.rule for d in diagnostics}
        assert "SAFE001" not in codes
        assert "ALWAYS001" in codes

    def test_file_level_noqa_suppresses_all(self, load_fixture):
        """G-11: file-level # pydocfix: noqa suppresses all diagnostics."""
        source = load_fixture("file_noqa.py")
        diagnostics, _, _ = check_file(source, _PATH, _registry(SAFE001(Config())))

        assert not any(d.rule == "SAFE001" for d in diagnostics)

    def test_noqa_becomes_unused_after_fix_emits_noq001(self, load_fixture):
        """G-12: noqa directive that becomes unused after fix triggers NOQ001."""
        source = load_fixture("noqa_after_fix.py")
        rules_map = make_registry(SAFE001(Config()), UNSAFE001(Config()))
        diagnostics, fixed, _ = check_file(
            source,
            _PATH,
            rules_map.type_to_rules,
            fix=True,
            known_rule_codes=rules_map.all_codes(),
        )

        assert any(d.rule == "NOQ001" and "UNSAFE001" in d.message for d in diagnostics)
        assert fixed is not None


class TestCheckFileSymbols:
    """G-13: symbol annotation on diagnostics."""

    def test_symbols_assigned_correctly(self, load_fixture):
        """G-13: module, class, method, and function docstrings get correct symbols."""
        source = load_fixture("symbols.py")
        diagnostics, _, _ = check_file(source, _PATH, _registry(SAFE001(Config())))

        symbols = {d.symbol for d in diagnostics}
        assert "" in symbols  # module-level docstring
        assert "MyClass" in symbols
        assert "MyClass.my_method" in symbols
        assert "top_level" in symbols
