"""Tests for CLS103: class docstring has an Args section (class_docstring_style='init')."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.cls.cls103 import cls103

from ..conftest import check_rule, load_fixture

CATEGORY = "cls"


class TestCLS103:
    def _rules(self):
        return [cls103]

    def test_rule(self, snapshot):
        fixture = load_fixture("cls103.py", CATEGORY)
        assert (
            check_rule(
                fixture,
                self._rules(),
                display_path="cls103.py",
                unsafe_fixes=True,
                config=Config(class_docstring_style="init"),
            )
            == snapshot
        )
