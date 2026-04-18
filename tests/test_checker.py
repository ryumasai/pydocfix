"""Tests for the checker module."""

from __future__ import annotations

from pathlib import Path

from pydocstring import PlainDocstring

from pydocfix.checker import check_file
from pydocfix.config import Config
from pydocfix.rules._base import Applicability, BaseRule, DiagnoseContext, Fix, replace_token
from pydocfix.rules.sum.sum002 import SUM002
from tests.helpers import make_type_to_rules

DUMMY_PATH = Path("test_dummy.py")


def _type_to_rules(*rules):
    return make_type_to_rules(*rules)


class SUP001(BaseRule[PlainDocstring]):
    """Synthetic rule used to test noqa usage tracking."""

    code = "SUP001"

    def diagnose(self, node: PlainDocstring, ctx: DiagnoseContext):
        if node.summary is not None and "x" in node.summary.text:
            yield self._make_diagnostic(ctx, "Contains x", target=node.summary)


class FIX001(BaseRule[PlainDocstring]):
    """Synthetic fix rule that removes 'x' from summary text."""

    code = "FIX001"

    def diagnose(self, node: PlainDocstring, ctx: DiagnoseContext):
        if node.summary is None or "x" not in node.summary.text:
            return
        fixed = node.summary.text.replace("x", "y")
        fix = Fix(
            edits=[replace_token(node.summary, fixed)],
            applicability=Applicability.SAFE,
        )
        yield self._make_diagnostic(ctx, "Replace x with y", fix=fix, target=node.summary)


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

    def test_noq001_uses_post_fix_state_for_inline_noqa(self):
        """Inline noqa becomes unused after fixes and should emit NOQ001."""
        source = '''\
def greet():
    """x"""  # noqa: SUP001
    pass
'''
        config = Config(skip_short_docstrings=False)
        rules = _type_to_rules(SUP001(config), FIX001(config))
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
