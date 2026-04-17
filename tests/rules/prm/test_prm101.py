"""Tests for PRM101: Docstring parameter type doesn't match type hint."""

from __future__ import annotations

from pydocfix.rules.prm.prm101 import PRM101

from ..conftest import check_rule, load_fixture

CATEGORY = "prm"


class TestPRM101:
    def _rules(self):
        return [PRM101()]

    def test_rule(self, snapshot):
        fixture = load_fixture("prm101.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="prm101.py", unsafe_fixes=True) == snapshot
