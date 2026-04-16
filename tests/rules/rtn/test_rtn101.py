"""Tests for RTN101: Docstring return type doesn't match type hint."""

from __future__ import annotations

from pydocfix.rules import Applicability
from pydocfix.rules.rtn.rtn101 import RTN101

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "rtn"


class TestRTN101:
    """Test cases for RTN101."""

    def test_violation_basic(self):
        """Docstring return type differs from signature annotation triggers RTN101."""
        fixture = load_fixture("rtn101_violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [RTN101()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "RTN101"
        assert diagnostics[0].fix is not None
        assert diagnostics[0].fix.applicability == Applicability.UNSAFE
        assert "'str'" in diagnostics[0].message
        assert "'int'" in diagnostics[0].message

    def test_no_violation(self):
        """Matching return types or no docstring type should not trigger."""
        fixture = load_fixture("rtn101_no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [RTN101()])

        assert len(diagnostics) == 0

    def test_fix_replaces_return_type(self):
        """Auto-fix should replace the wrong docstring return type."""
        fixture = load_fixture("rtn101_violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [RTN101()], fix=True, unsafe_fixes=True)

        assert fixed is not None
        assert "int:" in fixed
        assert "str:" not in fixed

    def test_fix_idempotent(self, tmp_path):
        """Applying fix twice produces no further violations."""
        fixture = load_fixture("rtn101_violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [RTN101()], fix=True, unsafe_fixes=True)
        assert fixed is not None

        temp = tmp_path / "fixed.py"
        temp.write_text(fixed)
        diagnostics2, _, _ = check_fixture_file(temp, [RTN101()])

        assert len(diagnostics2) == 0


class TestRTN101Snapshot:
    """Snapshot tests for RTN101 auto-fix."""

    def test_fix_basic(self, snapshot):
        """Fix replaces the wrong return type with the correct one."""
        fixture = load_fixture("rtn101_violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [RTN101()], fix=True, unsafe_fixes=True)

        assert fixed is not None
        assert fixed == snapshot
