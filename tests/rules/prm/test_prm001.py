"""Tests for PRM001: Function has parameters but no Args/Parameters section."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.prm.prm001 import PRM001

from ..conftest import check_rule, load_fixture

CATEGORY = "prm"


class TestPRM001:
    def _rules(self):
        return [PRM001(Config(skip_short_docstrings=False))]

    def test_rule(self, snapshot):
        fixture = load_fixture("prm001.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="prm001.py", unsafe_fixes=True) == snapshot
