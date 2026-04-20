"""Tests for CLS202: __init__ docstring has a Yields section."""

from __future__ import annotations

from pydocfix.rules.cls.cls202 import cls202

from ..conftest import check_rule, load_fixture

CATEGORY = "cls"


class TestCLS202:
    def _rules(self):
        return [cls202]

    def test_rule(self, snapshot):
        fixture = load_fixture("cls202.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="cls202.py") == snapshot
