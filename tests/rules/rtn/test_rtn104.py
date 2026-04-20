"""Tests for RTN104: Redundant return type in docstring (type_annotation_style = "signature")."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.rtn.rtn104 import rtn104

from ..conftest import check_rule, load_fixture

CATEGORY = "rtn"


class TestRTN104:
    def _rules(self):
        return [rtn104]

    def test_rule(self, snapshot):
        fixture = load_fixture("rtn104.py", CATEGORY)
        assert (
            check_rule(
                fixture, self._rules(), display_path="rtn104.py", config=Config(type_annotation_style="signature")
            )
            == snapshot
        )
