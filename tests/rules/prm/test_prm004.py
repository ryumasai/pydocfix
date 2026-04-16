"""Tests for PRM004: Missing parameter in docstring."""

from __future__ import annotations

from pydocfix.rules import Applicability
from pydocfix.rules.prm.prm004 import PRM004

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "prm"


class TestPRM004:
    """Test cases for PRM004."""

    def test_violation_basic(self):
        """Function with undocumented parameter triggers PRM004."""
        fixture = load_fixture("prm004_violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [PRM004()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "PRM004"
        assert diagnostics[0].fix is not None
        assert diagnostics[0].fix.applicability == Applicability.UNSAFE

    def test_no_violation(self):
        """Function with all parameters documented should not trigger."""
        fixture = load_fixture("prm004_no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [PRM004()])

        assert len(diagnostics) == 0

    def test_fix_adds_missing_entry(self):
        """Auto-fix should add an entry for the missing parameter."""
        fixture = load_fixture("prm004_violation_basic.py", CATEGORY)
        diagnostics, fixed, original = check_fixture_file(fixture, [PRM004()], fix=True, unsafe_fixes=True)

        assert len(diagnostics) == 1
        assert fixed is not None
        assert "y" in fixed

    def test_fix_produces_output(self):
        """Applying fix produces changed source (even if not fully convergent)."""
        fixture = load_fixture("prm004_violation_basic.py", CATEGORY)
        _, fixed, original = check_fixture_file(fixture, [PRM004()], fix=True, unsafe_fixes=True)
        assert fixed is not None
        assert fixed != original


class TestPRM004Snapshot:
    """Snapshot tests for PRM004 auto-fix."""

    def test_fix_basic(self, snapshot):
        """Fix inserts a stub entry for the missing parameter."""
        fixture = load_fixture("prm004_violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [PRM004()], fix=True, unsafe_fixes=True)

        assert fixed is not None
        assert fixed == snapshot
