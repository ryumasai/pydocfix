"""Tests for YLD104: Redundant yield type in docstring (type_annotation_style = "signature")."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.yld.yld104 import YLD104

from ..conftest import check_rule, load_fixture

CATEGORY = "yld"


class TestYLD104:
    def _rules(self):
        return [YLD104(Config(type_annotation_style="signature"))]

    def test_rule(self, snapshot):
        fixture = load_fixture("yld104.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="yld104.py") == snapshot
