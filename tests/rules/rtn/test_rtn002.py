"""Tests for RTN002: Returns section present but function doesn't return a value."""

from __future__ import annotations

from pydocfix.rules.rtn.rtn002 import RTN002

from ..conftest import check_rule, load_fixture

CATEGORY = "rtn"


class TestRTN002:
    def _rules(self):
        return [RTN002()]

    def test_rule(self, snapshot):
        fixture = load_fixture("rtn002.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="rtn002.py") == snapshot
