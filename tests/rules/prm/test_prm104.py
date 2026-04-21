"""Tests for PRM104: Redundant type in docstring (type_annotation_style = "signature")."""

from __future__ import annotations

from pydocfix.rules.prm.prm104 import prm104

from ..conftest import check_rule, load_fixture

CATEGORY = "prm"


class TestPRM104:
    def _rules(self):
        return [prm104]

    def test_rule(self, snapshot):
        fixture = load_fixture("prm104.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="prm104.py") == snapshot
