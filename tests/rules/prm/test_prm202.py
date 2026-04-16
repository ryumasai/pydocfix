"""Tests for PRM202: Parameter with default value missing 'default' in docstring."""

from __future__ import annotations

from pydocfix.rules import Applicability
from pydocfix.rules.prm.prm202 import PRM202

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "prm"


class TestPRM202:
    """Test cases for PRM202."""

    def test_violation_basic(self):
        """Default param without default value mention in description triggers PRM202."""
        fixture = load_fixture("prm202_violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [PRM202()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "PRM202"
        assert diagnostics[0].fix is not None
        assert diagnostics[0].fix.applicability == Applicability.UNSAFE

    def test_no_violation(self):
        """Default param with default mention or required param should not trigger."""
        fixture = load_fixture("prm202_no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [PRM202()])

        assert len(diagnostics) == 0

    def test_fix_adds_default_note(self):
        """Auto-fix should append 'Defaults to X.' to the description."""
        fixture = load_fixture("prm202_violation_basic.py", CATEGORY)
        _, fixed, original = check_fixture_file(fixture, [PRM202()], fix=True, unsafe_fixes=True)

        assert fixed is not None
        assert "42" in fixed


class TestPRM202Snapshot:
    """Snapshot tests for PRM202 auto-fix."""

    def test_fix_basic(self, snapshot):
        """Fix appends 'Defaults to X.' to the parameter description."""
        fixture = load_fixture("prm202_violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [PRM202()], fix=True, unsafe_fixes=True)

        assert fixed is not None
        assert fixed == snapshot
