"""Tests for CLS204: __init__ docstring has a Raises section (class_docstring_style='class')."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.cls.cls204 import cls204

from ..conftest import check_rule, load_fixture

CATEGORY = "cls"


class TestCLS204:
    def _rules(self):
        return [cls204]

    def test_rule(self, snapshot):
        fixture = load_fixture("cls204.py", CATEGORY)
        assert (
            check_rule(
                fixture,
                self._rules(),
                display_path="cls204.py",
                unsafe_fixes=True,
                config=Config(class_docstring_style="class"),
            )
            == snapshot
        )
