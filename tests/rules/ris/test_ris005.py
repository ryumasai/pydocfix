"""Tests for RIS005: Exception documented but not raised."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules import Applicability
from pydocfix.rules.ris.ris005 import RIS005

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "ris"


class TestRIS005:
    """Test cases for RIS005."""

    def _rule(self) -> RIS005:
        return RIS005(Config())

    def test_violation_basic(self):
        """Exception documented but not raised triggers RIS005."""
        fixture = load_fixture("ris005_violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "RIS005"
        assert diagnostics[0].fix is not None
        assert diagnostics[0].fix.applicability == Applicability.UNSAFE

    def test_no_violation(self):
        """All documented exceptions raised should not trigger."""
        fixture = load_fixture("ris005_no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 0
