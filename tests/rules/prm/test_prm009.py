"""Tests for PRM009: Parameter name missing * or ** prefix."""

from __future__ import annotations

from pydocfix.rules.prm.prm009 import prm009

from ..conftest import check_rule, load_fixture

CATEGORY = "prm"


class TestPRM009:
    def _rules(self):
        return [prm009]

    def test_rule(self, snapshot):
        fixture = load_fixture("prm009.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="prm009.py") == snapshot
