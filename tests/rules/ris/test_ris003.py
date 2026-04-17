"""Tests for RIS003: Raises entry has no description."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.ris.ris003 import RIS003

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "ris"


class TestRIS003:
    """Test cases for RIS003."""

    def _rule(self) -> RIS003:
        return RIS003(Config())

    def test_violation_basic(self):
        """Raises entry with empty description triggers RIS003."""
        fixture = load_fixture("ris003/violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "RIS003"
        assert diagnostics[0].fix is None

    def test_no_violation(self):
        """Raises entry with description should not trigger."""
        fixture = load_fixture("ris003/no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 0
