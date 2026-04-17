"""Tests for RIS002: Function has Raises section but doesn't raise."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.ris.ris002 import RIS002

from ..conftest import check_rule, load_fixture

CATEGORY = "ris"


class TestRIS002:
    def _rules(self):
        return [RIS002(Config())]

    def test_rule(self, snapshot):
        fixture = load_fixture("ris002.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="ris002.py") == snapshot
