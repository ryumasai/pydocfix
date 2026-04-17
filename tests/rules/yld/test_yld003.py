"""Tests for YLD003: Yields section has no description."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.yld.yld003 import YLD003

from ..conftest import check_rule, load_fixture

CATEGORY = "yld"


class TestYLD003:
    def _rules(self):
        return [YLD003(Config())]

    def test_rule(self, snapshot):
        fixture = load_fixture("yld003.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="yld003.py") == snapshot
