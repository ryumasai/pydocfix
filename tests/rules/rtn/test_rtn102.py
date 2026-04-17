"""Tests for RTN102: Return type not in docstring or signature."""

from __future__ import annotations

from pydocfix.rules.rtn.rtn102 import RTN102

from ..conftest import check_rule, load_fixture

CATEGORY = "rtn"


class TestRTN102:
    def _rules(self):
        return [RTN102()]

    def test_rule(self, snapshot):
        fixture = load_fixture("rtn102.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="rtn102.py") == snapshot
