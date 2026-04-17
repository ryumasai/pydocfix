"""Tests for PRM104: Redundant type in docstring (type_annotation_style = "signature")."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.prm.prm104 import PRM104

from ..conftest import check_rule, load_fixture

CATEGORY = "prm"


class TestPRM104:
    def _rules(self):
        return [PRM104(Config(type_annotation_style="signature"))]

    def test_rule(self, snapshot):
        fixture = load_fixture("prm104.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="prm104.py") == snapshot
