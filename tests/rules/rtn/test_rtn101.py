"""Tests for RTN101: Docstring return type doesn't match type hint."""

from __future__ import annotations

from pydocfix.rules.rtn.rtn101 import rtn101

from ..conftest import check_rule, load_fixture

CATEGORY = "rtn"


class TestRTN101:
    def _rules(self):
        return [rtn101]

    def test_rule(self, snapshot):
        fixture = load_fixture("rtn101.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="rtn101.py", unsafe_fixes=True) == snapshot
