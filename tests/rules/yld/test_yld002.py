"""Tests for YLD002: Non-generator function has Yields section."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules import Applicability
from pydocfix.rules.yld.yld002 import YLD002

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "yld"


class TestYLD002:
    """Test cases for YLD002."""

    def _rule(self) -> YLD002:
        return YLD002(Config())

    def test_violation_basic(self):
        """Non-generator with Yields section triggers YLD002."""
        fixture = load_fixture("yld002/violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "YLD002"
        assert diagnostics[0].fix is not None
        assert diagnostics[0].fix.applicability == Applicability.SAFE

    def test_no_violation(self):
        """Generator with Yields section or non-generator without section should not trigger."""
        fixture = load_fixture("yld002/no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 0

    def test_fix_removes_yields_section(self):
        """Auto-fix should remove the Yields section."""
        fixture = load_fixture("yld002/violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [self._rule()], fix=True)

        assert fixed is not None
        assert "Yields:" not in fixed


class TestYLD002Snapshot:
    """Snapshot tests for YLD002 auto-fix."""

    def test_fix_basic(self, snapshot):
        """Snapshot test for YLD002 fix."""
        fixture = load_fixture("yld002/violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [YLD002(Config())], fix=True)
        assert fixed == snapshot
