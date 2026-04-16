"""Tests for RTN003: Returns section has no description."""

from __future__ import annotations

from pydocfix.rules.rtn.rtn003 import RTN003

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "rtn"


class TestRTN003:
    """Test cases for RTN003."""

    def test_violation_basic(self):
        """Returns entry with empty description triggers RTN003."""
        fixture = load_fixture("rtn003_violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [RTN003()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "RTN003"
        assert diagnostics[0].fix is None

    def test_no_violation(self):
        """Returns entry with description should not trigger."""
        fixture = load_fixture("rtn003_no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [RTN003()])

        assert len(diagnostics) == 0
