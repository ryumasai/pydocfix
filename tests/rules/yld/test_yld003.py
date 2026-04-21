"""Tests for YLD003: Yields section has no description."""

from __future__ import annotations

from pydocfix.rules.yld.yld003 import yld003

from ..conftest import check_rule, load_fixture

CATEGORY = "yld"


class TestYLD003:
    def _rules(self):
        return [yld003]

    def test_rule(self, snapshot):
        fixture = load_fixture("yld003.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="yld003.py") == snapshot
