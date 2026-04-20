"""Tests for CLS201: __init__ docstring has a Returns section."""

from __future__ import annotations

from pydocfix.rules.cls.cls201 import CLS201

from ..conftest import check_rule, load_fixture

CATEGORY = "cls"


class TestCLS201:
    def _rules(self):
        return [CLS201()]

    def test_rule(self, snapshot):
        fixture = load_fixture("cls201.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="cls201.py") == snapshot
