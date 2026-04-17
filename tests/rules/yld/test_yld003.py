"""Tests for YLD003: Yields section has no description."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.yld.yld003 import YLD003

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "yld"


class TestYLD003:
    """Test cases for YLD003."""

    def _rule(self) -> YLD003:
        return YLD003(Config())

    def test_violation_basic(self):
        """Yields entry with empty description triggers YLD003."""
        fixture = load_fixture("yld003/violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "YLD003"
        assert diagnostics[0].fix is None

    def test_no_violation(self):
        """Yields entry with description should not trigger."""
        fixture = load_fixture("yld003/no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 0
