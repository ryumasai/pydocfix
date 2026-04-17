"""Tests for PRM009: Parameter name missing * or ** prefix."""

from __future__ import annotations

from pydocfix.rules import Applicability
from pydocfix.rules.prm.prm009 import PRM009

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "prm"


class TestPRM009:
    """Test cases for PRM009."""

    def test_violation_basic(self):
        """*args/**kwargs documented without prefix triggers PRM009."""
        fixture = load_fixture("prm009/violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [PRM009()])

        assert len(diagnostics) == 2
        assert all(d.rule == "PRM009" for d in diagnostics)
        assert all(d.fix is not None for d in diagnostics)
        assert all(d.fix.applicability == Applicability.SAFE for d in diagnostics)

    def test_no_violation(self):
        """*args/**kwargs with proper prefix should not trigger."""
        fixture = load_fixture("prm009/no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [PRM009()])

        assert len(diagnostics) == 0

    def test_fix_adds_prefix(self):
        """Auto-fix should add * or ** prefix to documented name."""
        fixture = load_fixture("prm009/violation_basic.py", CATEGORY)
        _, fixed, original = check_fixture_file(fixture, [PRM009()], fix=True)

        assert fixed is not None
        assert "*args" in fixed
        assert "**kwargs" in fixed

    def test_fix_idempotent(self, tmp_path):
        """Applying fix twice produces no further violations."""
        fixture = load_fixture("prm009/violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [PRM009()], fix=True)
        assert fixed is not None

        temp = tmp_path / "fixed.py"
        temp.write_text(fixed)
        diagnostics2, _, _ = check_fixture_file(temp, [PRM009()])

        assert len(diagnostics2) == 0


class TestPRM009Snapshot:
    """Snapshot tests for PRM009 auto-fix."""

    def test_fix_basic(self, snapshot):
        """Fix adds * and ** prefixes to varargs/kwargs entries."""
        fixture = load_fixture("prm009/violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [PRM009()], fix=True)

        assert fixed is not None
        assert fixed == snapshot
