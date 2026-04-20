"""Tests for PRM001: Function has parameters but no Args/Parameters section."""

from __future__ import annotations

from pydocfix.config import Config
from pydocfix.rules.prm.prm001 import prm001

from ..conftest import check_rule, load_fixture

CATEGORY = "prm"


class TestPRM001:
    def _rules(self):
        return [prm001]

    def test_rule(self, snapshot):
        fixture = load_fixture("prm001.py", CATEGORY)
        assert (
            check_rule(
                fixture,
                self._rules(),
                display_path="prm001.py",
                unsafe_fixes=True,
                config=Config(skip_short_docstrings=False),
            )
            == snapshot
        )

    def test_class_docstring_style_guard(self, snapshot):
        fixture = load_fixture("prm001_class_style.py", CATEGORY)
        assert (
            check_rule(
                fixture,
                [prm001],
                display_path="prm001_class_style.py",
                unsafe_fixes=True,
                config=Config(skip_short_docstrings=False, class_docstring_style="class"),
            )
            == snapshot
        )

    def test_class_docstring_style_guard_init(self, snapshot):
        fixture = load_fixture("prm001_init_style.py", CATEGORY)
        assert (
            check_rule(
                fixture,
                [prm001],
                display_path="prm001_init_style.py",
                unsafe_fixes=True,
                config=Config(skip_short_docstrings=False, class_docstring_style="init"),
            )
            == snapshot
        )
