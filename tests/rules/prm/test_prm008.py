"""Tests for PRM008: Docstring parameter has empty description."""

from __future__ import annotations

from pydocfix.rules.prm.prm008 import PRM008

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "prm"


class TestPRM008:
    """Test cases for PRM008."""

    def test_violation_basic(self):
        """Parameter with empty description triggers PRM008."""
        fixture = load_fixture("prm008/violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [PRM008()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "PRM008"
        assert diagnostics[0].fix is None

    def test_no_violation(self):
        """Parameter with description should not trigger."""
        fixture = load_fixture("prm008/no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [PRM008()])

        assert len(diagnostics) == 0
