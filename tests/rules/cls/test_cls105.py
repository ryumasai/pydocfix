"""Tests for CLS105: class docstring missing Args section (class_docstring_style='class')."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.cls.cls105 import cls105

from ..conftest import check_rule, load_fixture

CATEGORY = "cls"


class TestCLS105:
    def _rules(self):
        return [cls105]

    def test_rule(self, snapshot):
        fixture = load_fixture("cls105.py", CATEGORY)
        assert (
            check_rule(
                fixture,
                self._rules(),
                display_path="cls105.py",
                unsafe_fixes=True,
                config=Config(class_docstring_style="class"),
            )
            == snapshot
        )
