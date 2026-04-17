"""Tests for PRM002: Function has no parameters but docstring has Args section."""

from __future__ import annotations

from pydocfix.rules.prm.prm002 import PRM002

from ..conftest import check_rule, load_fixture

CATEGORY = "prm"


class TestPRM002:
    def _rules(self):
        return [PRM002()]

    def test_rule(self, snapshot):
        fixture = load_fixture("prm002.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="prm002.py") == snapshot
