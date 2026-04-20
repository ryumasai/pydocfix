"""Tests for PRM004: Missing parameter in docstring."""

from __future__ import annotations

from pydocfix.rules.prm.prm004 import prm004

from ..conftest import check_rule, load_fixture

CATEGORY = "prm"


class TestPRM004:
    def _rules(self):
        return [prm004]

    def test_rule(self, snapshot):
        fixture = load_fixture("prm004.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="prm004.py", unsafe_fixes=True) == snapshot
