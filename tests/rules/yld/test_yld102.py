"""Tests for YLD102: Yield type not in docstring or signature."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.yld.yld102 import YLD102

from ..conftest import check_rule, load_fixture

CATEGORY = "yld"


class TestYLD102:
    def _rules(self):
        return [YLD102(Config())]

    def test_rule(self, snapshot):
        fixture = load_fixture("yld102.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="yld102.py") == snapshot
