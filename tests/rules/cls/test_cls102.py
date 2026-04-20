"""Tests for CLS102: class docstring has a Yields section."""

from __future__ import annotations

from pydocfix.rules.cls.cls102 import CLS102

from ..conftest import check_rule, load_fixture

CATEGORY = "cls"


class TestCLS102:
    def _rules(self):
        return [CLS102()]

    def test_rule(self, snapshot):
        fixture = load_fixture("cls102.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="cls102.py") == snapshot
