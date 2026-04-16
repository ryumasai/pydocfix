"""Tests for noqa interaction with plugin rules."""

from __future__ import annotations

from pathlib import Path

from pydocfix.checker import build_rules_map, check_file
from pydocfix.config import Config
from pydocfix.rules._base import BaseRule, DiagnoseContext, Diagnostic


class PLUGNOQA001(BaseRule):
    """Test plugin rule for noqa suppression testing."""

    code = "PLUGNOQA001"
    enabled_by_default = True

    def diagnose(self, node, ctx: DiagnoseContext):
        yield Diagnostic(
            rule=self.code,
            message="Plugin violation",
            line=ctx.location.line,
            col=ctx.location.col,
            fix=None,
            symbol=ctx.symbol,
        )


class TestPluginNoqa:
    """Tests for noqa suppression with plugin rules."""

    def test_inline_noqa_suppresses_plugin(self):
        """Inline noqa suppresses plugin rule violation."""
        source = '''\
def foo():
    """Docstring."""  # noqa: PLUGNOQA001
    pass
'''
        config = Config(skip_short_docstrings=False)
        rules = build_rules_map([PLUGNOQA001(config)])
        diagnostics, _, _ = check_file(
            source,
            Path("test.py"),
            rules,
            config=config,
            known_rule_codes=frozenset({"PLUGNOQA001"}),
        )

        assert not any(d.rule == "PLUGNOQA001" for d in diagnostics)

    def test_blanket_noqa_suppresses_plugin(self):
        """Blanket noqa suppresses all violations including plugin."""
        source = '''\
def foo():
    """Docstring."""  # noqa
    pass
'''
        config = Config(skip_short_docstrings=False)
        rules = build_rules_map([PLUGNOQA001(config)])
        diagnostics, _, _ = check_file(
            source,
            Path("test.py"),
            rules,
            config=config,
        )

        assert not any(d.rule == "PLUGNOQA001" for d in diagnostics)

    def test_specific_noqa_does_not_suppress_other_rule(self):
        """Specific noqa code only suppresses that code."""
        from pydocfix.rules.sum.sum002 import SUM002

        source = '''\
def foo():
    """No period"""  # noqa: PLUGNOQA001
    pass
'''
        config = Config(skip_short_docstrings=False)
        rules = build_rules_map([PLUGNOQA001(config), SUM002(config)])
        diagnostics, _, _ = check_file(
            source,
            Path("test.py"),
            rules,
            config=config,
            known_rule_codes=frozenset({"PLUGNOQA001", "SUM002"}),
        )

        codes = {d.rule for d in diagnostics}
        assert "PLUGNOQA001" not in codes
        assert "SUM002" in codes
