"""Tests for PRM006: Docstring parameters in different order than signature."""

from __future__ import annotations

from pydocfix.rules.prm.prm006 import PRM006

from ..conftest import check_rule, load_fixture

CATEGORY = "prm"


class TestPRM006:
    def _rules(self):
        return [PRM006()]

    def test_rule(self, snapshot):
        fixture = load_fixture("prm006.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="prm006.py", unsafe_fixes=True) == snapshot
