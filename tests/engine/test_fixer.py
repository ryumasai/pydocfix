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

    def test_fixes_missing_period(self, load_test_fixture):
        """Fixes missing period violation."""
        source = load_test_fixture("greet_no_period.py").read_text(encoding="utf-8")
        config = Config(skip_short_docstrings=False)
        rules = make_type_to_rules(SUM002(config))
        _, fixed, _ = check_file(source, DUMMY_PATH, rules, fix=True, config=config)

        assert fixed is not None
        assert '"""Say hello."""' in fixed

    def test_no_fix_needed(self, load_test_fixture):
        """Returns None for fixed_source when nothing to fix."""
        source = load_test_fixture("greet_with_period.py").read_text(encoding="utf-8")
        config = Config(skip_short_docstrings=False)
        rules = make_type_to_rules(SUM002(config))
        _, fixed, _ = check_file(source, DUMMY_PATH, rules, fix=True, config=config)

        assert fixed is None

    def test_preserves_surrounding_code(self, load_test_fixture):
        """Fix preserves code around fixed docstring."""
        source = load_test_fixture("preserve_surrounding.py").read_text(encoding="utf-8")
        config = Config(skip_short_docstrings=False)
        rules = make_type_to_rules(SUM002(config))
        _, fixed, _ = check_file(source, DUMMY_PATH, rules, fix=True, config=config)

        assert fixed is not None
        assert "import os" in fixed
        assert 'return "hello"' in fixed
        assert "x = 42" in fixed

    def test_no_fix_without_flag(self, load_test_fixture):
        """Does not fix when fix=False."""
        source = load_test_fixture("greet_no_period.py").read_text(encoding="utf-8")
        config = Config(skip_short_docstrings=False)
        rules = make_type_to_rules(SUM002(config))
        _, fixed, _ = check_file(source, DUMMY_PATH, rules, fix=False, config=config)

        assert fixed is None

    def test_fix_idempotent(self, load_test_fixture, tmp_path):
        """Applying fix twice produces same result."""
        source = load_test_fixture("greet_no_period.py").read_text(encoding="utf-8")
        config = Config(skip_short_docstrings=False)
        rules = make_type_to_rules(SUM002(config))

        _, fixed1, _ = check_file(source, DUMMY_PATH, rules, fix=True, config=config)
        assert fixed1 is not None
        _, fixed2, _ = check_file(fixed1, DUMMY_PATH, rules, fix=True, config=config)

        assert fixed2 is None  # No more changes needed
