"""Tests for CLS206: __init__ docstring missing Raises section (class_docstring_style='init')."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.cls.cls206 import CLS206

from ..conftest import check_rule, load_fixture

CATEGORY = "cls"


class TestCLS206:
    def _rules(self):
        return [CLS206(Config(class_docstring_style="init"))]

    def test_rule(self, snapshot):
        fixture = load_fixture("cls206.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="cls206.py", unsafe_fixes=True) == snapshot
