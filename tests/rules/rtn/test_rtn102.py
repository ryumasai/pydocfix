"""Tests for RTN102: Return type not in docstring or signature."""

from __future__ import annotations

from pydocfix.rules.rtn.rtn102 import RTN102

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "rtn"


class TestRTN102:
    """Test cases for RTN102."""

    def test_violation_basic(self):
        """Returns entry with no type in either docstring or signature triggers RTN102."""
        fixture = load_fixture("rtn102/violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [RTN102()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "RTN102"
        assert diagnostics[0].fix is None

    def test_no_violation(self):
        """Return type present in signature or docstring should not trigger."""
        fixture = load_fixture("rtn102/no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [RTN102()])

        assert len(diagnostics) == 0
