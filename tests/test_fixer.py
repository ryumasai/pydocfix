"""Tests for fixer integration."""

from __future__ import annotations

from pathlib import Path

from pydocfix.checker import check_file
from pydocfix.config import Config
from pydocfix.rules.sum.sum002 import SUM002
from tests.helpers import make_type_to_rules

DUMMY_PATH = Path("test.py")


class TestFixer:
    """Tests for fix integration in check_file."""

    def test_fixes_missing_period(self):
        """Fixes missing period violation."""
        source = '''\
def greet():
    """Say hello"""
    pass
'''
        config = Config(skip_short_docstrings=False)
        rules = make_type_to_rules(SUM002(config))
        _, fixed, _ = check_file(source, DUMMY_PATH, rules, fix=True, config=config)

        assert fixed is not None
        assert '"""Say hello."""' in fixed

    def test_no_fix_needed(self):
        """Returns None for fixed_source when nothing to fix."""
        source = '''\
def greet():
    """Say hello."""
    pass
'''
        config = Config(skip_short_docstrings=False)
        rules = make_type_to_rules(SUM002(config))
        _, fixed, _ = check_file(source, DUMMY_PATH, rules, fix=True, config=config)

        assert fixed is None

    def test_preserves_surrounding_code(self):
        """Fix preserves code around fixed docstring."""
        source = '''\
import os

def greet():
    """Say hello"""
    return "hello"

x = 42
'''
        config = Config(skip_short_docstrings=False)
        rules = make_type_to_rules(SUM002(config))
        _, fixed, _ = check_file(source, DUMMY_PATH, rules, fix=True, config=config)

        assert fixed is not None
        assert "import os" in fixed
        assert 'return "hello"' in fixed
        assert "x = 42" in fixed

    def test_no_fix_without_flag(self):
        """Does not fix when fix=False."""
        source = '''\
def greet():
    """Say hello"""
    pass
'''
        config = Config(skip_short_docstrings=False)
        rules = make_type_to_rules(SUM002(config))
        _, fixed, _ = check_file(source, DUMMY_PATH, rules, fix=False, config=config)

        assert fixed is None

    def test_fix_idempotent(self, tmp_path):
        """Applying fix twice produces same result."""
        source = '''\
def greet():
    """Say hello"""
    pass
'''
        config = Config(skip_short_docstrings=False)
        rules = make_type_to_rules(SUM002(config))

        _, fixed1, _ = check_file(source, DUMMY_PATH, rules, fix=True, config=config)
        assert fixed1 is not None
        _, fixed2, _ = check_file(fixed1, DUMMY_PATH, rules, fix=True, config=config)

        assert fixed2 is None  # No more changes needed
