"""Tests for RIS002: Function has Raises section but doesn't raise."""

from __future__ import annotations

from pydocfix.rules.ris.ris002 import ris002

from ..conftest import check_rule, load_fixture

CATEGORY = "ris"


class TestRIS002:
    def _rules(self):
        return [ris002]

    def test_rule(self, snapshot):
        fixture = load_fixture("ris002.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="ris002.py") == snapshot
