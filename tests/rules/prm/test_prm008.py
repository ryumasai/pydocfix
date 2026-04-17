"""Tests for PRM008: Docstring parameter has empty description."""

from __future__ import annotations

from pydocfix.rules.prm.prm008 import PRM008

from ..conftest import check_rule, load_fixture

CATEGORY = "prm"


class TestPRM008:
    def _rules(self):
        return [PRM008()]

    def test_rule(self, snapshot):
        fixture = load_fixture("prm008.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="prm008.py") == snapshot
