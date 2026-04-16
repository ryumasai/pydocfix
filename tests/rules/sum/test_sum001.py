"""Tests for SUM001: Docstring has no summary line."""

from __future__ import annotations

from pydocfix.rules.sum.sum001 import SUM001

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "sum"


class TestSUM001:
    """Test cases for SUM001: missing summary line."""

    def test_violation_basic(self):
        """Docstring with only sections and no summary triggers SUM001."""
        fixture = load_fixture("sum001_violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [SUM001()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "SUM001"
        assert diagnostics[0].fix is None

    def test_no_violation(self):
        """Valid docstrings with summaries should not trigger."""
        fixture = load_fixture("sum001_no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [SUM001()])

        assert len(diagnostics) == 0
