"""Tests for RIS001: Function raises but has no Raises section."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules import Applicability
from pydocfix.rules.ris.ris001 import RIS001

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "ris"


class TestRIS001:
    """Test cases for RIS001."""

    def _rule(self) -> RIS001:
        return RIS001(Config(skip_short_docstrings=False))

    def test_violation_basic(self):
        """Function that raises without Raises section triggers RIS001."""
        fixture = load_fixture("ris001_violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "RIS001"
        assert diagnostics[0].fix is not None
        assert diagnostics[0].fix.applicability == Applicability.UNSAFE

    def test_no_violation(self):
        """Function with Raises section or no raises should not trigger."""
        fixture = load_fixture("ris001_no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 0
