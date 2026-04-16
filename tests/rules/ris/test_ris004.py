"""Tests for RIS004: Exception raised but not documented."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules import Applicability
from pydocfix.rules.ris.ris004 import RIS004

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "ris"


class TestRIS004:
    """Test cases for RIS004."""

    def _rule(self) -> RIS004:
        return RIS004(Config())

    def test_violation_basic(self):
        """Exception raised but not in Raises section triggers RIS004."""
        fixture = load_fixture("ris004_violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "RIS004"
        assert diagnostics[0].fix is not None
        assert diagnostics[0].fix.applicability == Applicability.UNSAFE

    def test_no_violation(self):
        """All raised exceptions documented should not trigger."""
        fixture = load_fixture("ris004_no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 0
