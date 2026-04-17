"""Tests for PRM003: Docstring documents self or cls."""

from __future__ import annotations

from pydocfix.rules import Applicability
from pydocfix.rules.prm.prm003 import PRM003

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "prm"


class TestPRM003:
    """Test cases for PRM003."""

    def test_violation_basic(self):
        """Method that documents self triggers PRM003."""
        fixture = load_fixture("prm003/violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [PRM003()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "PRM003"
        assert diagnostics[0].fix is not None
        assert diagnostics[0].fix.applicability == Applicability.SAFE

    def test_no_violation(self):
        """Method that does not document self/cls should not trigger."""
        fixture = load_fixture("prm003/no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [PRM003()])

        assert len(diagnostics) == 0

    def test_fix_removes_self_entry(self):
        """Auto-fix should remove the self entry."""
        fixture = load_fixture("prm003/violation_basic.py", CATEGORY)
        diagnostics, fixed, original = check_fixture_file(fixture, [PRM003()], fix=True)

        assert len(diagnostics) == 1
        assert fixed is not None
        # self entry should be gone, x entry should remain
        assert "self:" not in fixed
        assert "x" in fixed

    def test_fix_idempotent(self, tmp_path):
        """Applying fix twice produces no further violations."""
        fixture = load_fixture("prm003/violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [PRM003()], fix=True)
        assert fixed is not None

        temp = tmp_path / "fixed.py"
        temp.write_text(fixed)
        diagnostics2, _, _ = check_fixture_file(temp, [PRM003()])

        assert len(diagnostics2) == 0


class TestPRM003Snapshot:
    """Snapshot tests for PRM003 auto-fix."""

    def test_fix_basic(self, snapshot):
        """Fix removes the self documentation entry."""
        fixture = load_fixture("prm003/violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [PRM003()], fix=True)

        assert fixed is not None
        assert fixed == snapshot
