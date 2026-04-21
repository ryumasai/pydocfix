"""Tests for checker integration."""

from __future__ import annotations

from pathlib import Path

from pydocfix.engine.checker import check_file
from tests.engine._rules.always001 import always001
from tests.engine._rules.cyclic001 import cyclic001
from tests.engine._rules.safe000 import safe000
from tests.engine._rules.safe001 import safe001
from tests.engine._rules.unsafe001 import unsafe001
from tests.helpers import make_registry

_PATH = Path("test.py")


def _registry(*rule_fns):
    """Build a RuleRegistry from rule functions."""
    return make_registry(*rule_fns)


class TestCheckFileBasic:
    """basic detection and syntax error handling."""

    def test_empty_file_returns_empty(self, load_fixture):
        """completely empty source file produces no diagnostics."""
        source = load_fixture("empty_file.py")
        diagnostics, fixed, _ = check_file(source, _PATH, _registry(safe001))

        assert diagnostics == []
        assert fixed is None

    def test_no_docstrings_returns_empty(self, load_fixture):
        """source with functions but no docstrings produces no diagnostics."""
        source = load_fixture("no_docstrings.py")
        diagnostics, _, _ = check_file(source, _PATH, _registry(safe001))

        assert diagnostics == []

    def test_detects_violation(self, load_fixture):
        """violation in docstring produces a diagnostic."""
        source = load_fixture("safe_violation.py")
        diagnostics, _, _ = check_file(source, _PATH, _registry(safe001))

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "SAFE001"

    def test_no_violation_returns_empty(self, load_fixture):
        """clean docstring produces no diagnostics."""
        source = load_fixture("no_violation.py")
        diagnostics, _, _ = check_file(source, _PATH, _registry(safe001))

        assert diagnostics == []

    def test_detects_all_violations_in_file(self, load_fixture):
        """every violating docstring in a file is diagnosed."""
        source = load_fixture("two_violations.py")
        diagnostics, _, _ = check_file(source, _PATH, _registry(safe001))

        assert len(diagnostics) == 2
        assert all(d.rule == "SAFE001" for d in diagnostics)

    def test_syntax_error_returns_empty(self):
        """source with a syntax error returns empty diagnostics and no fix."""
        source = "def broken(\n"
        diagnostics, fixed, _ = check_file(source, _PATH, _registry(safe001))

        assert diagnostics == []
        assert fixed is None


class TestCheckFileFix:
    """fix application modes."""

    def test_no_fix_without_flag(self, load_fixture):
        """fix=False returns fixed_source=None."""
        source = load_fixture("safe_violation.py")
        _, fixed, _ = check_file(source, _PATH, _registry(safe001), fix=False)

        assert fixed is None

    def test_safe_fix_applied(self, load_fixture):
        """SAFE fix is applied when fix=True."""
        source = load_fixture("safe_violation.py")
        _, fixed, _ = check_file(source, _PATH, _registry(safe001), fix=True)

        assert fixed is not None
        assert "FIXED(SAFE001)" in fixed

    def test_unsafe_fix_not_applied_without_flag(self, load_fixture):
        """UNSAFE fix is not applied when unsafe_fixes=False."""
        source = load_fixture("unsafe_violation.py")
        _, fixed, _ = check_file(source, _PATH, _registry(unsafe001), fix=True, unsafe_fixes=False)

        assert fixed is None

    def test_unsafe_fix_applied_with_flag(self, load_fixture):
        """UNSAFE fix is applied when unsafe_fixes=True."""
        source = load_fixture("unsafe_violation.py")
        _, fixed, _ = check_file(source, _PATH, _registry(unsafe001), fix=True, unsafe_fixes=True)

        assert fixed is not None
        assert "FIXED(UNSAFE001)" in fixed


class TestCheckFileNoqa:
    """noqa suppression behaviour."""

    def test_blanket_noqa_suppresses_all(self, load_fixture):
        """# noqa (blanket) suppresses every rule."""
        source = load_fixture("blanket_noqa.py")
        diagnostics, _, _ = check_file(source, _PATH, _registry(always001))

        assert not any(d.rule == "ALWAYS001" for d in diagnostics)

    def test_specific_noqa_suppresses_only_listed_code(self, load_fixture):
        """# noqa: SAFE001 suppresses SAFE001 but leaves ALWAYS001 active."""
        source = load_fixture("specific_noqa.py")
        rules = _registry(safe001, always001)
        diagnostics, _, _ = check_file(source, _PATH, rules)

        codes = {d.rule for d in diagnostics}
        assert "SAFE001" not in codes
        assert "ALWAYS001" in codes

    def test_file_level_noqa_suppresses_all(self, load_fixture):
        """file-level # pydocfix: noqa suppresses all diagnostics."""
        source = load_fixture("file_noqa.py")
        diagnostics, _, _ = check_file(source, _PATH, _registry(safe001))

        assert not any(d.rule == "SAFE001" for d in diagnostics)

    def test_noqa_becomes_unused_after_fix_emits_noq001(self, load_fixture):
        """noqa directive that becomes unused after fix triggers NOQ001."""
        source = load_fixture("noqa_after_fix.py")
        rules_map = make_registry(safe001, unsafe001)
        diagnostics, fixed, _ = check_file(
            source,
            _PATH,
            rules_map,
            fix=True,
            known_rule_codes=rules_map.all_codes(),
        )

        assert any(d.rule == "NOQ001" and "UNSAFE001" in d.message for d in diagnostics)
        assert fixed is not None


class TestCheckFileSymbols:
    """symbol annotation on diagnostics."""

    def test_symbols_assigned_correctly(self, load_fixture):
        """module, class, method, and function docstrings get correct symbols."""
        source = load_fixture("symbols.py")
        diagnostics, _, _ = check_file(source, _PATH, _registry(safe001))

        symbols = {d.symbol for d in diagnostics}
        assert "" in symbols  # module-level docstring
        assert "MyClass" in symbols
        assert "MyClass.my_method" in symbols
        assert "top_level" in symbols


class TestCheckFileFixConvergence:
    """fix convergence loop behaviour."""

    def test_non_converging_fix_logs_warning_and_returns_partial(self, load_fixture, caplog):
        """a fix that re-introduces violations hits the iteration limit and logs a warning."""
        import logging

        source = load_fixture("cyclic_violation.py")
        with caplog.at_level(logging.WARNING):
            diagnostics, fixed, _ = check_file(source, _PATH, _registry(cyclic001), fix=True)

        assert any("converge" in r.message for r in caplog.records)
        assert fixed is not None  # partial fix was still applied


class TestCheckFileOverlappingFix:
    """overlapping fix skipping behaviour."""

    def test_overlapping_fix_is_skipped_with_warning(self, load_fixture, caplog):
        """when two rules propose fixes over the same token, the second is skipped."""
        import logging

        source = load_fixture("safe_violation.py")
        # SAFE000 and SAFE001 both target the same summary token in safe_violation.py.
        # Whichever is processed second will be skipped due to overlap.
        with caplog.at_level(logging.WARNING):
            diagnostics, fixed, _ = check_file(source, _PATH, _registry(safe000, safe001), fix=True)

        assert any("skipping fix" in r.message for r in caplog.records)
        # Exactly one fix was applied — the docstring changed but only once.
        assert fixed is not None
        applied = {t for t in ["FIXED(SAFE000)", "FIXED(SAFE001)"] if t in fixed}
        assert len(applied) == 1


class TestCheckFileRemainingAfterFix:
    """third return value: diagnostics remaining after fix."""

    def test_unsafe_fix_skipped_stays_in_remaining(self, load_fixture):
        """an UNSAFE violation not fixed due to unsafe_fixes=False appears in remaining."""
        source = load_fixture("unsafe_violation.py")
        _, _, remaining = check_file(source, _PATH, _registry(unsafe001), fix=True, unsafe_fixes=False)

        assert any(d.rule == "UNSAFE001" for d in remaining)

    def test_safe_fix_applied_not_in_remaining(self, load_fixture):
        """a SAFE violation that was fixed does not appear in remaining."""
        source = load_fixture("safe_violation.py")
        _, _, remaining = check_file(source, _PATH, _registry(safe001), fix=True)

        assert not any(d.rule == "SAFE001" for d in remaining)


class TestCheckFileUnusedNoqa:
    """unused noqa directives trigger NOQ001."""

    def test_unused_blanket_noqa_emits_noq001(self, load_fixture):
        """blanket # noqa with no violations below triggers NOQ001."""
        source = load_fixture("unused_blanket_noqa.py")
        rules_map = make_registry(safe001)
        diagnostics, _, _ = check_file(
            source,
            _PATH,
            rules_map,
            known_rule_codes=rules_map.all_codes(),
        )

        assert any(d.rule == "NOQ001" for d in diagnostics)

    def test_partial_noqa_rewritten_after_fix(self, load_fixture):
        """# noqa: SAFE001, EXTERNAL001 is rewritten to # noqa: EXTERNAL001 when SAFE001 is unused."""
        source = load_fixture("partial_noqa_rewrite.py")
        rules_map = make_registry(safe001)
        diagnostics, fixed, _ = check_file(
            source,
            _PATH,
            rules_map,
            fix=True,
            known_rule_codes=rules_map.all_codes(),
        )

        assert any(d.rule == "NOQ001" for d in diagnostics)
        assert fixed is not None
        assert "# noqa: EXTERNAL001" in fixed
        assert "SAFE001" not in fixed
