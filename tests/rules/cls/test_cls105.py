"""Tests for CLS105: class docstring missing Args section (class_docstring_style='class')."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.cls.cls105 import CLS105

from ..conftest import check_rule, load_fixture

CATEGORY = "cls"


class TestCLS105:
    def _rules(self):
        return [CLS105(Config(class_docstring_style="class"))]

    def test_rule(self, snapshot):
        fixture = load_fixture("cls105.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="cls105.py", unsafe_fixes=True) == snapshot
