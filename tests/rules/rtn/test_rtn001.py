"""Tests for RTN001: Function has return annotation but no Returns section."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.rtn.rtn001 import RTN001

from ..conftest import check_rule, load_fixture

CATEGORY = "rtn"


class TestRTN001:
    def _rules(self):
        return [RTN001(Config(skip_short_docstrings=False))]

    def test_rule(self, snapshot):
        fixture = load_fixture("rtn001.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="rtn001.py", unsafe_fixes=True) == snapshot
