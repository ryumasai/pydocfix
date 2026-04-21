"""Tests for CLS001: __init__ has its own docstring but the class also has one."""

from __future__ import annotations

from pydocfix.rules.cls.cls001 import cls001

from ..conftest import check_rule, load_fixture

CATEGORY = "cls"


class TestCLS001:
    def _rules(self):
        return [cls001]

    def test_rule(self, snapshot):
        fixture = load_fixture("cls001.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="cls001.py") == snapshot
