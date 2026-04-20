"""Tests for PRM202: Parameter with default value missing 'default' in docstring."""

from __future__ import annotations

from pydocfix.rules.prm.prm202 import prm202

from ..conftest import check_rule, load_fixture

CATEGORY = "prm"


class TestPRM202:
    def _rules(self):
        return [prm202]

    def test_rule(self, snapshot):
        fixture = load_fixture("prm202.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="prm202.py", unsafe_fixes=True) == snapshot
