"""Tests for PRM005: Docstring has parameter not in function signature."""

from __future__ import annotations

from pydocfix.rules import Applicability
from pydocfix.rules.prm.prm005 import PRM005

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "prm"


class TestPRM005:
    """Test cases for PRM005."""

    def test_violation_basic(self):
        """Documented parameter not in signature triggers PRM005."""
        fixture = load_fixture("prm005_violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [PRM005()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "PRM005"
        assert diagnostics[0].fix is not None
        assert diagnostics[0].fix.applicability == Applicability.UNSAFE

    def test_no_violation(self):
        """All documented parameters exist in signature, should not trigger."""
        fixture = load_fixture("prm005_no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [PRM005()])

        assert len(diagnostics) == 0

    def test_fix_removes_nonexistent_entry(self):
        """Auto-fix should remove the entry for the non-existent parameter."""
        fixture = load_fixture("prm005_violation_basic.py", CATEGORY)
        diagnostics, fixed, original = check_fixture_file(fixture, [PRM005()], fix=True, unsafe_fixes=True)

        assert len(diagnostics) == 1
        assert fixed is not None
        assert "z" not in fixed

    def test_fix_idempotent(self, tmp_path):
        """Applying fix twice produces no further violations."""
        fixture = load_fixture("prm005_violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [PRM005()], fix=True, unsafe_fixes=True)
        assert fixed is not None

        temp = tmp_path / "fixed.py"
        temp.write_text(fixed)
        diagnostics2, _, _ = check_fixture_file(temp, [PRM005()])

        assert len(diagnostics2) == 0


class TestPRM005Snapshot:
    """Snapshot tests for PRM005 auto-fix."""

    def test_fix_basic(self, snapshot):
        """Fix removes the extraneous parameter entry."""
        fixture = load_fixture("prm005_violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [PRM005()], fix=True, unsafe_fixes=True)

        assert fixed is not None
        assert fixed == snapshot
