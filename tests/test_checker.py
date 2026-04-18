"""Tests for the checker module."""

from __future__ import annotations

from pathlib import Path

from pydocfix.checker import check_file
from pydocfix.config import Config
from pydocfix.rules.sum.sum002 import SUM002
from tests.helpers import make_type_to_rules

DUMMY_PATH = Path("test_dummy.py")


def _type_to_rules(*rules):
    return make_type_to_rules(*rules)


class TestCheckFile:
    """Tests for check_file()."""

    def test_detects_violation(self):
        """check_file detects a violation."""
        source = '''\
def greet():
    """Say hello"""
    pass
'''
        config = Config(skip_short_docstrings=False)
        rules = _type_to_rules(SUM002(config))
        diagnostics, _, _ = check_file(source, DUMMY_PATH, rules, config=config)

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "SUM002"

    def test_reports_correct_line(self):
        """Diagnostics report correct line number."""
        source = '''\
def foo():
    pass

def bar():
    """No period"""
    pass
'''
        config = Config(skip_short_docstrings=False)
        rules = _type_to_rules(SUM002(config))
        diagnostics, _, _ = check_file(source, DUMMY_PATH, rules, config=config)

        assert len(diagnostics) == 1
        assert diagnostics[0].range.start.lineno == 5

    def test_no_violation(self):
        """check_file returns empty list when no violations."""
        source = '''\
def greet():
    """Say hello."""
    pass
'''
        config = Config(skip_short_docstrings=False)
        rules = _type_to_rules(SUM002(config))
        diagnostics, _, _ = check_file(source, DUMMY_PATH, rules, config=config)

        assert len(diagnostics) == 0

    def test_multiple_functions(self):
        """check_file detects violations in multiple functions."""
        source = '''\
def foo():
    """No period"""
    pass

def bar():
    """Also no period"""
    pass
'''
        config = Config(skip_short_docstrings=False)
        rules = _type_to_rules(SUM002(config))
        diagnostics, _, _ = check_file(source, DUMMY_PATH, rules, config=config)

        assert len(diagnostics) == 2

    def test_syntax_error_returns_empty(self):
        """check_file handles syntax errors gracefully."""
        source = "def broken(\n"
        rules = _type_to_rules(SUM002(Config()))
        diagnostics, fixed, remaining = check_file(source, DUMMY_PATH, rules)

        assert diagnostics == []
        assert fixed is None
        assert remaining == []

    def test_fix_applied(self):
        """check_file applies safe fix when fix=True."""
        source = '''\
def greet():
    """Say hello"""
    pass
'''
        config = Config(skip_short_docstrings=False)
        rules = _type_to_rules(SUM002(config))
        _, fixed, _ = check_file(source, DUMMY_PATH, rules, fix=True, config=config)

        assert fixed is not None
        assert "hello." in fixed

    def test_no_fix_without_flag(self):
        """check_file does not fix when fix=False."""
        source = '''\
def greet():
    """Say hello"""
    pass
'''
        config = Config(skip_short_docstrings=False)
        rules = _type_to_rules(SUM002(config))
        _, fixed, _ = check_file(source, DUMMY_PATH, rules, config=config)

        assert fixed is None
