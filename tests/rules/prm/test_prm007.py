"""Tests for PRM007: Duplicate parameter in docstring."""

from __future__ import annotations

from pydocfix.rules.prm.prm007 import prm007

from ..conftest import check_rule, load_fixture

CATEGORY = "prm"


class TestPRM007:
    def _rules(self):
        return [prm007]

    def test_rule(self, snapshot):
        fixture = load_fixture("prm007.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="prm007.py", unsafe_fixes=True) == snapshot
