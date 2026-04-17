"""Tests for PRM102: Parameter has no type in docstring or signature."""

from __future__ import annotations

from pydocfix.rules.prm.prm102 import PRM102

from ..conftest import check_fixture_file, load_fixture

CATEGORY = "prm"


class TestPRM102:
    """Test cases for PRM102."""

    def test_violation_basic(self):
        """Parameter with no type anywhere triggers PRM102."""
        fixture = load_fixture("prm102/violation_basic.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [PRM102()])

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "PRM102"
        assert diagnostics[0].fix is None

    def test_no_violation(self):
        """Parameter with type in signature or docstring should not trigger."""
        fixture = load_fixture("prm102/no_violation.py", CATEGORY)
        diagnostics, _, _ = check_fixture_file(fixture, [PRM102()])

        assert len(diagnostics) == 0
