"""Tests for YLD101: Docstring yield type doesn't match type hint."""

from __future__ import annotations

from pydocfix.rules.yld.yld101 import yld101

from ..conftest import check_rule, load_fixture

CATEGORY = "yld"


class TestYLD101:
    def _rules(self):
        return [yld101]

    def test_rule(self, snapshot):
        fixture = load_fixture("yld101.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="yld101.py", unsafe_fixes=True) == snapshot
