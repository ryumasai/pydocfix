"""Tests for PRM006: Docstring parameters in different order than signature."""

from __future__ import annotations

from pydocfix.rules import Applicability
from pydocfix.rules.prm.prm006 import PRM006

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "prm"


class TestPRM006:
    """Test cases for PRM006."""

    def test_violation_basic(self):
        """Parameters in wrong order triggers PRM006."""
        fixture = load_fixture("prm006/violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [PRM006()])

        # May produce one or more violations depending on how many params are out of order
        assert len(diagnostics) >= 1
        assert all(d.rule == "PRM006" for d in diagnostics)
        assert diagnostics[0].fix is not None
        assert diagnostics[0].fix.applicability == Applicability.UNSAFE

    def test_no_violation(self):
        """Parameters in correct order should not trigger."""
        fixture = load_fixture("prm006/no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [PRM006()])

        assert len(diagnostics) == 0

    def test_fix_reorders_parameters(self):
        """Auto-fix should reorder parameters to match signature order."""
        fixture = load_fixture("prm006/violation_basic.py", CATEGORY)
        diagnostics, fixed, original = check_fixture_file(fixture, [PRM006()], fix=True, unsafe_fixes=True)

        assert len(diagnostics) >= 1
        assert fixed is not None
        assert fixed.index("x") < fixed.index("y")

    def test_fix_idempotent(self, tmp_path):
        """Applying fix twice produces no further violations."""
        fixture = load_fixture("prm006/violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [PRM006()], fix=True, unsafe_fixes=True)
        assert fixed is not None

        temp = tmp_path / "fixed.py"
        temp.write_text(fixed)
        diagnostics2, _, _ = check_fixture_file(temp, [PRM006()])

        assert len(diagnostics2) == 0


class TestPRM006Snapshot:
    """Snapshot tests for PRM006 auto-fix."""

    def test_fix_basic(self, snapshot):
        """Fix reorders parameters to match the function signature."""
        fixture = load_fixture("prm006/violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [PRM006()], fix=True, unsafe_fixes=True)

        assert fixed is not None
        assert fixed == snapshot
