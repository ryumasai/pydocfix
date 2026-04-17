"""Tests for YLD105: Yield has no annotation in signature (type_annotation_style = "signature")."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.yld.yld105 import YLD105

from ..conftest import check_rule, load_fixture

CATEGORY = "yld"


class TestYLD105:
    def _rules(self):
        return [YLD105(Config(type_annotation_style="signature"))]

    def test_rule(self, snapshot):
        fixture = load_fixture("yld105.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="yld105.py") == snapshot
