"""Tests for PRM007: Duplicate parameter in docstring."""

from __future__ import annotations

from pydocfix.rules import Applicability
from pydocfix.rules.prm.prm007 import PRM007

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "prm"


class TestPRM007:
    """Test cases for PRM007."""

    def test_violation_basic(self):
        """Duplicate parameter in docstring triggers PRM007."""
        fixture = load_fixture("prm007_violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [PRM007()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "PRM007"
        assert diagnostics[0].fix is not None
        assert diagnostics[0].fix.applicability == Applicability.UNSAFE

    def test_no_violation(self):
        """Unique parameter entries should not trigger."""
        fixture = load_fixture("prm007_no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [PRM007()])

        assert len(diagnostics) == 0

    def test_fix_removes_duplicate(self):
        """Auto-fix should remove the duplicate entry."""
        fixture = load_fixture("prm007_violation_basic.py", CATEGORY)
        diagnostics, fixed, original = check_fixture_file(fixture, [PRM007()], fix=True, unsafe_fixes=True)

        assert len(diagnostics) == 1
        assert fixed is not None
        assert fixed != original

    def test_fix_idempotent(self, tmp_path):
        """Applying fix twice produces no further violations."""
        fixture = load_fixture("prm007_violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [PRM007()], fix=True, unsafe_fixes=True)
        assert fixed is not None

        temp = tmp_path / "fixed.py"
        temp.write_text(fixed)
        diagnostics2, _, _ = check_fixture_file(temp, [PRM007()])

        assert len(diagnostics2) == 0


class TestPRM007Snapshot:
    """Snapshot tests for PRM007 auto-fix."""

    def test_fix_basic(self, snapshot):
        """Fix removes the duplicate parameter entry."""
        fixture = load_fixture("prm007_violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [PRM007()], fix=True, unsafe_fixes=True)

        assert fixed is not None
        assert fixed == snapshot
