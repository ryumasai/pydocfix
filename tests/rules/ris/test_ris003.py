"""Tests for RIS003: Raises entry has no description."""

from __future__ import annotations

from pydocfix.rules.ris.ris003 import ris003

from ..conftest import check_rule, load_fixture

CATEGORY = "ris"


class TestRIS003:
    def _rules(self):
        return [ris003]

    def test_rule(self, snapshot):
        fixture = load_fixture("ris003.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="ris003.py") == snapshot
