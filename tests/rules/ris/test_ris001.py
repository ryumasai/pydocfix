"""Tests for RIS001: Function raises but has no Raises section."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.ris.ris001 import RIS001

from ..conftest import check_rule, load_fixture

CATEGORY = "ris"


class TestRIS001:
    def _rules(self):
        return [RIS001(Config(skip_short_docstrings=False))]

    def test_rule(self, snapshot):
        fixture = load_fixture("ris001.py", CATEGORY)
        assert check_rule(fixture, self._rules(), display_path="ris001.py", unsafe_fixes=True) == snapshot

    def test_class_docstring_style_guard(self, snapshot):
        rules = [RIS001(Config(skip_short_docstrings=False, class_docstring_style="class"))]
        fixture = load_fixture("ris001_class_style.py", CATEGORY)
        assert check_rule(fixture, rules, display_path="ris001_class_style.py", unsafe_fixes=True) == snapshot

    def test_class_docstring_style_guard_init(self, snapshot):
        rules = [RIS001(Config(skip_short_docstrings=False, class_docstring_style="init"))]
        fixture = load_fixture("ris001_init_style.py", CATEGORY)
        assert check_rule(fixture, rules, display_path="ris001_init_style.py", unsafe_fixes=True) == snapshot
