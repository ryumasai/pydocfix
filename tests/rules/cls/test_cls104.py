"""Tests for CLS104: class docstring has a Raises section (class_docstring_style='init')."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.cls.cls104 import CLS104

from ..conftest import check_rule, load_fixture

CATEGORY = "cls"


class TestCLS104:
    def _rules(self):
        return [CLS104(Config(class_docstring_style="init"))]

    def test_rule(self, snapshot):
        fixture = load_fixture("cls104.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="cls104.py", unsafe_fixes=True) == snapshot
