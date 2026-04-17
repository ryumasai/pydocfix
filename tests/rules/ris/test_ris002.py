"""Tests for RIS002: Function has Raises section but doesn't raise."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules import Applicability
from pydocfix.rules.ris.ris002 import RIS002

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "ris"


class TestRIS002:
    """Test cases for RIS002."""

    def _rule(self) -> RIS002:
        return RIS002(Config())

    def test_violation_basic(self):
        """Non-raising function with Raises section triggers RIS002."""
        fixture = load_fixture("ris002/violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "RIS002"
        assert diagnostics[0].fix is not None
        assert diagnostics[0].fix.applicability == Applicability.SAFE

    def test_no_violation(self):
        """Function that raises with section or neither should not trigger."""
        fixture = load_fixture("ris002/no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 0

    def test_fix_removes_raises_section(self):
        """Auto-fix should remove the Raises section."""
        fixture = load_fixture("ris002/violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [self._rule()], fix=True)

        assert fixed is not None
        assert "Raises:" not in fixed


class TestRIS002Snapshot:
    """Snapshot tests for RIS002 auto-fix."""

    def test_fix_basic(self, snapshot):
        """Snapshot test for RIS002 fix."""
        fixture = load_fixture("ris002/violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [RIS002(Config())], fix=True)
        assert fixed == snapshot
