"""Tests for YLD001: Generator function has no Yields section."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules import Applicability
from pydocfix.rules.yld.yld001 import YLD001

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "yld"


class TestYLD001:
    """Test cases for YLD001."""

    def _rule(self) -> YLD001:
        return YLD001(Config(skip_short_docstrings=False))

    def test_violation_basic(self):
        """Generator function without Yields section triggers YLD001."""
        fixture = load_fixture("yld001/violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) >= 1
        assert all(d.rule == "YLD001" for d in diagnostics)
        assert diagnostics[0].fix is not None
        assert diagnostics[0].fix.applicability == Applicability.UNSAFE

    def test_no_violation(self):
        """Generator with Yields section or non-generator should not trigger."""
        fixture = load_fixture("yld001/no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [self._rule()])

        assert len(diagnostics) == 0
