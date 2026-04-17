"""Tests for RTN003: Returns section has no description."""

from __future__ import annotations

from pydocfix.rules.rtn.rtn003 import RTN003

from ..conftest import check_rule, load_fixture

CATEGORY = "rtn"


class TestRTN003:
    def _rules(self):
        return [RTN003()]

    def test_rule(self, snapshot):
        fixture = load_fixture("rtn003.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="rtn003.py") == snapshot
