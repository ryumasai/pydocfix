"""Tests for CLS106: class docstring missing Raises section (class_docstring_style='class')."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.cls.cls106 import CLS106

from ..conftest import check_rule, load_fixture

CATEGORY = "cls"


class TestCLS106:
    def _rules(self):
        return [CLS106(Config(class_docstring_style="class"))]

    def test_rule(self, snapshot):
        fixture = load_fixture("cls106.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="cls106.py", unsafe_fixes=True) == snapshot
