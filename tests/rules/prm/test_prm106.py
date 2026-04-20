"""Tests for PRM106: Parameter has signature annotation (type_annotation_style = "docstring")."""

from __future__ import annotations

from pydocfix.rules.prm.prm106 import prm106

from ..conftest import check_rule, load_fixture

CATEGORY = "prm"


class TestPRM106:
    def _rules(self):
        return [prm106]

    def test_rule(self, snapshot):
        fixture = load_fixture("prm106.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="prm106.py") == snapshot
