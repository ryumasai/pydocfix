"""Tests for PRM003: Docstring documents self or cls."""

from __future__ import annotations

from pydocfix.rules.prm.prm003 import PRM003

from ..conftest import check_rule, load_fixture

CATEGORY = "prm"


class TestPRM003:
    def _rules(self):
        return [PRM003()]

    def test_rule(self, snapshot):
        fixture = load_fixture("prm003.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="prm003.py") == snapshot
