"""Tests for RIS004: Exception raised but not documented."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.ris.ris004 import RIS004

from ..conftest import check_rule, load_fixture

CATEGORY = "ris"


class TestRIS004:
    def _rules(self):
        return [RIS004(Config())]

    def test_rule(self, snapshot):
        fixture = load_fixture("ris004.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="ris004.py", unsafe_fixes=True) == snapshot
