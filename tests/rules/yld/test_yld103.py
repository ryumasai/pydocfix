"""Tests for YLD103: Yield has no type in docstring (type_annotation_style = "docstring")."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.yld.yld103 import yld103

from ..conftest import check_rule, load_fixture

CATEGORY = "yld"


class TestYLD103:
    def _rules(self):
        return [yld103]

    def test_rule(self, snapshot):
        fixture = load_fixture("yld103.py", CATEGORY)
        assert (
            check_rule(
                fixture,
                self._rules(),
                display_path="yld103.py",
                unsafe_fixes=True,
                config=Config(type_annotation_style="docstring"),
            )
            == snapshot
        )
