"""Tests for YLD001: Generator function has no Yields section."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.yld.yld001 import YLD001

from ..conftest import check_rule, load_fixture

CATEGORY = "yld"


class TestYLD001:
    def _rules(self):
        return [YLD001(Config(skip_short_docstrings=False))]

    def test_rule(self, snapshot):
        fixture = load_fixture("yld001.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="yld001.py", unsafe_fixes=True) == snapshot
