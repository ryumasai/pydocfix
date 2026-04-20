"""Tests for CLS205: __init__ docstring missing Args section (class_docstring_style='init')."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.cls.cls205 import CLS205

from ..conftest import check_rule, load_fixture

CATEGORY = "cls"


class TestCLS205:
    def _rules(self):
        return [CLS205(Config(class_docstring_style="init"))]

    def test_rule(self, snapshot):
        fixture = load_fixture("cls205.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="cls205.py", unsafe_fixes=True) == snapshot
