"""Tests for YLD002: Non-generator function has Yields section."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.yld.yld002 import YLD002

from ..conftest import check_rule, load_fixture

CATEGORY = "yld"


class TestYLD002:
    def _rules(self):
        return [YLD002(Config())]

    def test_rule(self, snapshot):
        fixture = load_fixture("yld002.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="yld002.py") == snapshot
