"""Tests for RTN106: Return has signature annotation (type_annotation_style = "docstring")."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.rtn.rtn106 import RTN106

from ..conftest import check_rule, load_fixture

CATEGORY = "rtn"


class TestRTN106:
    def _rules(self):
        return [RTN106(Config(type_annotation_style="docstring"))]

    def test_rule(self, snapshot):
        fixture = load_fixture("rtn106.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="rtn106.py") == snapshot
