"""Tests for PRM201: Parameter with default value missing 'optional' in docstring."""

from __future__ import annotations

from pydocfix.rules import Applicability
from pydocfix.rules.prm.prm201 import PRM201

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "prm"


class TestPRM201:
    """Test cases for PRM201."""

    def test_violation_basic(self):
        """Default param without 'optional' in docstring type triggers PRM201."""
        fixture = load_fixture("prm201_violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [PRM201()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "PRM201"
        assert diagnostics[0].fix is not None
        assert diagnostics[0].fix.applicability == Applicability.UNSAFE

    def test_no_violation(self):
        """Default param with 'optional' or required param should not trigger."""
        fixture = load_fixture("prm201_no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [PRM201()])

        assert len(diagnostics) == 0

    def test_fix_adds_optional(self):
        """Auto-fix should add 'optional' to the type annotation."""
        fixture = load_fixture("prm201_violation_basic.py", CATEGORY)
        _, fixed, original = check_fixture_file(fixture, [PRM201()], fix=True, unsafe_fixes=True)

        assert fixed is not None
        assert "optional" in fixed


class TestPRM201Snapshot:
    """Snapshot tests for PRM201 auto-fix."""

    def test_fix_basic(self, snapshot):
        """Fix inserts 'optional' into the type brackets."""
        fixture = load_fixture("prm201_violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [PRM201()], fix=True, unsafe_fixes=True)

        assert fixed is not None
        assert fixed == snapshot
