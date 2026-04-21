"""Tests for CLS203: __init__ docstring has an Args section (class_docstring_style='class')."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.cls.cls203 import cls203

from ..conftest import check_rule, load_fixture

CATEGORY = "cls"


class TestCLS203:
    def _rules(self):
        return [cls203]

    def test_rule(self, snapshot):
        fixture = load_fixture("cls203.py", CATEGORY)
        assert (
            check_rule(
                fixture,
                self._rules(),
                display_path="cls203.py",
                unsafe_fixes=True,
                config=Config(class_docstring_style="class"),
            )
            == snapshot
        )
