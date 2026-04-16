"""Tests for YLD101: Docstring yield type doesn't match type hint."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules import Applicability
from pydocfix.rules.yld.yld101 import YLD101

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "yld"


class TestYLD101:
    """Test cases for YLD101."""

    def _rule(self) -> YLD101:
        return YLD101(Config())

    def test_violation_basic(self):
        """Mismatched yield type in docstring triggers YLD101."""
        fixture = load_fixture("yld101_violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "YLD101"
        assert diagnostics[0].fix is not None
        assert diagnostics[0].fix.applicability == Applicability.UNSAFE

    def test_no_violation(self):
        """Matching yield types or no docstring type should not trigger."""
        fixture = load_fixture("yld101_no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 0


class TestYLD101Snapshot:
    """Snapshot tests for YLD101 auto-fix."""

    def test_fix_basic(self, snapshot):
        """Snapshot test for YLD101 fix."""
        fixture = load_fixture("yld101_violation_basic.py", CATEGORY)
        _, fixed, _ = check_fixture_file(fixture, [YLD101(Config())], unsafe_fixes=True)
        assert fixed == snapshot
