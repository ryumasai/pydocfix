"""Tests for PRM101: Docstring parameter type doesn't match type hint."""

from __future__ import annotations

from pydocfix.rules import Applicability
from pydocfix.rules.prm.prm101 import PRM101

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "prm"


class TestPRM101:
    """Test cases for PRM101."""

    def test_violation_basic(self):
        """Docstring type differs from signature annotation triggers PRM101."""
        fixture = load_fixture("prm101/violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [PRM101()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "PRM101"
        assert diagnostics[0].fix is not None
        assert diagnostics[0].fix.applicability == Applicability.UNSAFE
        assert "'str'" in diagnostics[0].message
        assert "'int'" in diagnostics[0].message

    def test_no_violation(self):
        """Matching types or no docstring type should not trigger."""
        fixture = load_fixture("prm101/no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [PRM101()])

        assert len(diagnostics) == 0

    def test_fix_replaces_type(self):
        """Auto-fix should replace the wrong docstring type with the correct one."""
        fixture = load_fixture("prm101/violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [PRM101()], fix=True, unsafe_fixes=True)

        assert fixed is not None
        assert "(int)" in fixed
        assert "(str)" not in fixed

    def test_fix_idempotent(self, tmp_path):
        """Applying fix twice produces no further violations."""
        fixture = load_fixture("prm101/violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [PRM101()], fix=True, unsafe_fixes=True)
        assert fixed is not None

        temp = tmp_path / "fixed.py"
        temp.write_text(fixed)
        diagnostics2, _, _ = check_fixture_file(temp, [PRM101()])

        assert len(diagnostics2) == 0


class TestPRM101Snapshot:
    """Snapshot tests for PRM101 auto-fix."""

    def test_fix_basic(self, snapshot):
        """Fix replaces the wrong docstring type with the signature type."""
        fixture = load_fixture("prm101/violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [PRM101()], fix=True, unsafe_fixes=True)

        assert fixed is not None
        assert fixed == snapshot
