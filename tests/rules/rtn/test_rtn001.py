"""Tests for RTN001: Function has return annotation but no Returns section."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules import Applicability
from pydocfix.rules.rtn.rtn001 import RTN001

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "rtn"


class TestRTN001:
    """Test cases for RTN001."""

    def _rule(self) -> RTN001:
        return RTN001(Config(skip_short_docstrings=False))

    def test_violation_basic(self):
        """Function with return annotation but no Returns section triggers RTN001."""
        fixture = load_fixture("rtn001_violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) >= 1
        assert diagnostics[0].rule == "RTN001"
        assert diagnostics[0].fix is not None
        assert diagnostics[0].fix.applicability == Applicability.UNSAFE

    def test_no_violation(self):
        """Function with Returns section or no annotation should not trigger."""
        fixture = load_fixture("rtn001_no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 0

    def test_fix_adds_returns_section(self):
        """Auto-fix should add a Returns section."""
        fixture = load_fixture("rtn001_violation_basic.py", CATEGORY)
        _, fixed, original = check_fixture_file(fixture, [self._rule()], fix=True, unsafe_fixes=True)

        assert fixed is not None
        assert fixed != original
        assert "Returns:" in fixed

    def test_fix_idempotent(self, tmp_path):
        """Applying fix twice produces no further violations."""
        fixture = load_fixture("rtn001_violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [self._rule()], fix=True, unsafe_fixes=True)
        assert fixed is not None

        temp = tmp_path / "fixed.py"
        temp.write_text(fixed)
        diagnostics2, _, _ = check_fixture_file(temp, [self._rule()])

        assert len(diagnostics2) == 0


class TestRTN001Snapshot:
    """Snapshot tests for RTN001 auto-fix."""

    def test_fix_basic(self, snapshot):
        """Fix adds a Returns section with the correct type."""
        fixture = load_fixture("rtn001_violation_basic.py", CATEGORY)
        rule = RTN001(Config(skip_short_docstrings=False))
        _, fixed, _ = check_fixture_file(fixture, [rule], fix=True, unsafe_fixes=True)

        assert fixed is not None
        assert fixed == snapshot
