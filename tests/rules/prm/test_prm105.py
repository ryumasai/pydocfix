"""Tests for PRM105: Parameter has no signature annotation (type_annotation_style = "signature")."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.prm.prm105 import PRM105

from ..conftest import check_rule, load_fixture

CATEGORY = "prm"


class TestPRM105:
    def _rules(self):
        return [PRM105(Config(type_annotation_style="signature"))]

    def test_rule(self, snapshot):
        fixture = load_fixture("prm105.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="prm105.py") == snapshot
