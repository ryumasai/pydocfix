"""Tests for PRM201: Parameter with default value missing 'optional' in docstring."""

from __future__ import annotations

from pydocfix.rules.prm.prm201 import prm201

from ..conftest import check_rule, load_fixture

CATEGORY = "prm"


class TestPRM201:
    def _rules(self):
        return [prm201]

    def test_rule(self, snapshot):
        fixture = load_fixture("prm201.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="prm201.py", unsafe_fixes=True) == snapshot
