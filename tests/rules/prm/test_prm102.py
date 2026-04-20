"""Tests for PRM102: Parameter has no type in docstring or signature."""

from __future__ import annotations

from pydocfix.rules.prm.prm102 import prm102

from ..conftest import check_rule, load_fixture

CATEGORY = "prm"


class TestPRM102:
    def _rules(self):
        return [prm102]

    def test_rule(self, snapshot):
        fixture = load_fixture("prm102.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="prm102.py") == snapshot
