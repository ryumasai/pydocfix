"""Tests for RIS003: Raises entry has no description."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.ris.ris003 import RIS003

from ..conftest import check_rule, load_fixture

CATEGORY = "ris"


class TestRIS003:
    def _rules(self):
        return [RIS003(Config())]

    def test_rule(self, snapshot):
        fixture = load_fixture("ris003.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="ris003.py") == snapshot
