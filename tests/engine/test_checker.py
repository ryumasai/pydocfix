"""Tests for the checker module."""

from __future__ import annotations

from pathlib import Path

from pydocfix.checker import check_file
from pydocfix.config import Config
from pydocfix.rules.sum.sum002 import SUM002
from tests.engine.synthetic_rules.fix001 import FIX001
from tests.engine.synthetic_rules.sup001 import SUP001
from tests.helpers import make_type_to_rules

DUMMY_PATH = Path("test_dummy.py")


class TestCheckFile:
    """Tests for check_file()."""

    def test_detects_violation(self, load_test_fixture):
        """check_file detects a violation."""
        source = load_test_fixture("greet_no_period.py").read_text(encoding="utf-8")
        config = Config(skip_short_docstrings=False)
        rules = make_type_to_rules(SUM002(config))
        diagnostics, _, _ = check_file(source, DUMMY_PATH, rules, config=config)

        assert len(diagnostics) == 1
        assert diagnostics[0].rule == "SUM002"

    def test_reports_correct_line(self, load_test_fixture):
        """Diagnostics report correct line number."""
        source = load_test_fixture("bar_no_period_offset.py").read_text(encoding="utf-8")
        config = Config(skip_short_docstrings=False)
        rules = make_type_to_rules(SUM002(config))
        diagnostics, _, _ = check_file(source, DUMMY_PATH, rules, config=config)

        assert len(diagnostics) == 1
        assert diagnostics[0].range.start.lineno == 6

    def test_no_violation(self, load_test_fixture):
        """check_file returns empty list when no violations."""
        source = load_test_fixture("greet_with_period.py").read_text(encoding="utf-8")
        config = Config(skip_short_docstrings=False)
        rules = make_type_to_rules(SUM002(config))
        diagnostics, _, _ = check_file(source, DUMMY_PATH, rules, config=config)

        assert len(diagnostics) == 0

    def test_multiple_functions(self, load_test_fixture):
        """check_file detects violations in multiple functions."""
        source = load_test_fixture("two_no_period.py").read_text(encoding="utf-8")
        config = Config(skip_short_docstrings=False)
        rules = make_type_to_rules(SUM002(config))
        diagnostics, _, _ = check_file(source, DUMMY_PATH, rules, config=config)

        assert len(diagnostics) == 2

    def test_syntax_error_returns_empty(self):
        """check_file handles syntax errors gracefully."""
        source = "def broken(\n"
        rules = make_type_to_rules(SUM002(Config()))
        diagnostics, fixed, remaining = check_file(source, DUMMY_PATH, rules)

        assert diagnostics == []
        assert fixed is None
        assert remaining == []

    def test_fix_applied(self, load_test_fixture):
        """check_file applies safe fix when fix=True."""
        source = load_test_fixture("greet_no_period.py").read_text(encoding="utf-8")
        config = Config(skip_short_docstrings=False)
        rules = make_type_to_rules(SUM002(config))
        _, fixed, _ = check_file(source, DUMMY_PATH, rules, fix=True, config=config)

        assert fixed is not None
        assert "hello." in fixed

    def test_no_fix_without_flag(self, load_test_fixture):
        """check_file does not fix when fix=False."""
        source = load_test_fixture("greet_no_period.py").read_text(encoding="utf-8")
        config = Config(skip_short_docstrings=False)
        rules = make_type_to_rules(SUM002(config))
        _, fixed, _ = check_file(source, DUMMY_PATH, rules, config=config)

        assert fixed is None

    def test_noq001_uses_post_fix_state_for_inline_noqa(self, load_test_fixture):
        """Inline noqa becomes unused after fixes and should emit NOQ001."""
        source = load_test_fixture("noqa_x_sup001.py").read_text(encoding="utf-8")
        config = Config(skip_short_docstrings=False)
        rules = make_type_to_rules(SUP001(config), FIX001(config))
        diagnostics, fixed, _ = check_file(
            source,
            DUMMY_PATH,
            rules,
            fix=True,
            config=config,
            known_rule_codes=frozenset({"SUP001", "FIX001"}),
        )

        assert any(d.rule == "NOQ001" and "SUP001" in d.message for d in diagnostics)
        assert fixed is not None
        assert "# noqa" not in fixed
