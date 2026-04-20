"""Tests for CLS101: class docstring has a Returns section."""

from __future__ import annotations

from pydocfix.rules.cls.cls101 import cls101

from ..conftest import check_rule, load_fixture

CATEGORY = "cls"


class TestCLS101:
    def _rules(self):
        return [cls101]

    def test_rule(self, snapshot):
        fixture = load_fixture("cls101.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="cls101.py") == snapshot
