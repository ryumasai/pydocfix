"""Tests for RIS005: Exception documented but not raised."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.ris.ris005 import RIS005

from ..conftest import check_rule, load_fixture

CATEGORY = "ris"


class TestRIS005:
    def _rules(self):
        return [RIS005(Config())]

    def test_rule(self, snapshot):
        fixture = load_fixture("ris005.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="ris005.py", unsafe_fixes=True) == snapshot
