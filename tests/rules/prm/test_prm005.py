"""Tests for PRM005: Docstring has parameter not in function signature."""

from __future__ import annotations

from pydocfix.rules.prm.prm005 import prm005

from ..conftest import check_rule, load_fixture

CATEGORY = "prm"


class TestPRM005:
    def _rules(self):
        return [prm005]

    def test_rule(self, snapshot):
        fixture = load_fixture("prm005.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="prm005.py", unsafe_fixes=True) == snapshot
