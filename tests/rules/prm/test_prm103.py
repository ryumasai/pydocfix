"""Tests for PRM103: Parameter has no type in docstring (type_annotation_style = "docstring")."""

from __future__ import annotations

from pydocfix.rules.prm.prm103 import prm103

from ..conftest import check_rule, load_fixture

CATEGORY = "prm"


class TestPRM103:
    def _rules(self):
        return [prm103]

    def test_rule(self, snapshot):
        fixture = load_fixture("prm103.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="prm103.py", unsafe_fixes=True) == snapshot
