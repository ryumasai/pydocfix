"""Tests for RIS001: Function raises but has no Raises section."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.ris.ris001 import RIS001

from ..conftest import check_rule, load_fixture

CATEGORY = "ris"


class TestRIS001:
    def _rules(self):
        return [RIS001(Config(skip_short_docstrings=False))]

    def test_rule(self, snapshot):
        fixture = load_fixture("ris001.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="ris001.py", unsafe_fixes=True) == snapshot
