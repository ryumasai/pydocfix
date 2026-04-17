"""Tests for YLD106: Yield has signature annotation (type_annotation_style = "docstring")."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.yld.yld106 import YLD106

from ..conftest import check_rule, load_fixture

CATEGORY = "yld"


class TestYLD106:
    def _rules(self):
        return [YLD106(Config(type_annotation_style="docstring"))]

    def test_rule(self, snapshot):
        fixture = load_fixture("yld106.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="yld106.py") == snapshot
