"""Tests for RTN105: Return has no annotation in signature (type_annotation_style = "signature")."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.rtn.rtn105 import rtn105

from ..conftest import check_rule, load_fixture

CATEGORY = "rtn"


class TestRTN105:
    def _rules(self):
        return [rtn105]

    def test_rule(self, snapshot):
        fixture = load_fixture("rtn105.py", CATEGORY)
        assert (
            check_rule(
                fixture, self._rules(), display_path="rtn105.py", config=Config(type_annotation_style="signature")
            )
            == snapshot
        )
