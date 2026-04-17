"""Tests for RTN103: Return has no type in docstring (type_annotation_style = "docstring")."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.rtn.rtn103 import RTN103

from ..conftest import check_rule, load_fixture

CATEGORY = "rtn"


class TestRTN103:
    def _rules(self):
        return [RTN103(Config(type_annotation_style="docstring"))]

    def test_rule(self, snapshot):
        fixture = load_fixture("rtn103.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="rtn103.py", unsafe_fixes=True) == snapshot
