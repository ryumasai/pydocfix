"""Tests for YLD102: Yield type not in docstring or signature."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.yld.yld102 import YLD102

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "yld"


class TestYLD102:
    """Test cases for YLD102."""

    def _rule(self) -> YLD102:
        return YLD102(Config())

    def test_violation_basic(self):
        """Yields entry with no type in docstring or signature triggers YLD102."""
        fixture = load_fixture("yld102/violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "YLD102"
        assert diagnostics[0].fix is None

    def test_no_violation(self):
        """Type in signature or docstring should not trigger."""
        fixture = load_fixture("yld102/no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 0
