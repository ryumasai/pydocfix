"""Tests for YLD002: Non-generator function has Yields section."""

from __future__ import annotations

from pydocfix.rules.yld.yld002 import yld002

from ..conftest import check_rule, load_fixture

CATEGORY = "yld"


class TestYLD002:
    def _rules(self):
        return [yld002]

    def test_rule(self, snapshot):
        fixture = load_fixture("yld002.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="yld002.py") == snapshot
