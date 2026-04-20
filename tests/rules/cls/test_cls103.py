"""Tests for CLS103: class docstring has an Args section (class_docstring_style='init')."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.cls.cls103 import CLS103

from ..conftest import check_rule, load_fixture

CATEGORY = "cls"


class TestCLS103:
    def _rules(self):
        return [CLS103(Config(class_docstring_style="init"))]

    def test_rule(self, snapshot):
        fixture = load_fixture("cls103.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="cls103.py", unsafe_fixes=True) == snapshot
