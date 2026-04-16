"""Tests for RTN002: Returns section present but function doesn't return a value."""

from __future__ import annotations

from pydocfix.rules import Applicability
from pydocfix.rules.rtn.rtn002 import RTN002

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "rtn"


class TestRTN002:
    """Test cases for RTN002."""

    def test_violation_basic(self):
        """Function with Returns section but no return value triggers RTN002."""
        fixture = load_fixture("rtn002_violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [RTN002()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "RTN002"
        assert diagnostics[0].fix is not None
        assert diagnostics[0].fix.applicability == Applicability.SAFE

    def test_no_violation(self):
        """Function that returns a value or has no Returns section should not trigger."""
        fixture = load_fixture("rtn002_no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [RTN002()])

        assert len(diagnostics) == 0

    def test_fix_removes_returns_section(self):
        """Auto-fix should remove the Returns section."""
        fixture = load_fixture("rtn002_violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [RTN002()], fix=True)

        assert fixed is not None
        assert "Returns:" not in fixed

    def test_fix_idempotent(self, tmp_path):
        """Applying fix twice produces no further violations."""
        fixture = load_fixture("rtn002_violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [RTN002()], fix=True)
        assert fixed is not None

        temp = tmp_path / "fixed.py"
        temp.write_text(fixed)
        diagnostics2, _, _ = check_fixture_file(temp, [RTN002()])

        assert len(diagnostics2) == 0


class TestRTN002Snapshot:
    """Snapshot tests for RTN002 auto-fix."""

    def test_fix_basic(self, snapshot):
        """Fix removes the extraneous Returns section."""
        fixture = load_fixture("rtn002_violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [RTN002()], fix=True)

        assert fixed is not None
        assert fixed == snapshot
