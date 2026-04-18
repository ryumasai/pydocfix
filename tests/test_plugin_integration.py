"""Tests for plugin integration with the checker."""

from __future__ import annotations

from pathlib import Path

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.checker import check_file
from pydocfix.config import Config
from pydocfix.rules._base import BaseRule, DiagnoseContext
from tests.helpers import make_type_to_rules


class TESTPLUGIN001(BaseRule[GoogleDocstring | NumPyDocstring | PlainDocstring]):
    """Test plugin rule that flags any short single-line docstring summary."""

    code = "TESTPLUGIN001"
    enabled_by_default = True

    def diagnose(self, node, ctx: DiagnoseContext):
        summary = node.summary
        if summary is not None and len(summary.text.strip()) < 5:
            yield self._make_diagnostic(ctx, "Docstring summary too short", target=node)


class TestPluginIntegration:
    """Tests for plugin rules integrated with check_file."""

    def test_plugin_rule_detects_violation(self):
        """Plugin rule can detect violations."""
        source = '''\
def foo():
    """Hi."""
    pass
'''
        config = Config(skip_short_docstrings=False)
        rules = make_type_to_rules(TESTPLUGIN001(config))
        diagnostics, _, _ = check_file(source, Path("test.py"), rules, config=config)

        assert any(d.rule == "TESTPLUGIN001" for d in diagnostics)

    def test_plugin_rule_no_violation(self):
        """Plugin rule does not flag longer docstrings."""
        source = '''\
def foo():
    """Do something very useful here."""
    pass
'''
        config = Config(skip_short_docstrings=False)
        rules = make_type_to_rules(TESTPLUGIN001(config))
        diagnostics, _, _ = check_file(source, Path("test.py"), rules, config=config)

        assert not any(d.rule == "TESTPLUGIN001" for d in diagnostics)

    def test_plugin_and_builtin_together(self):
        """Plugin rules work alongside built-in rules."""
        from pydocfix.rules.sum.sum002 import SUM002

        source = '''\
def foo():
    """Hi"""
    pass
'''
        config = Config(skip_short_docstrings=False)
        rules = make_type_to_rules(TESTPLUGIN001(config), SUM002(config))
        diagnostics, _, _ = check_file(source, Path("test.py"), rules, config=config)

        codes = {d.rule for d in diagnostics}
        assert "SUM002" in codes
        assert "TESTPLUGIN001" in codes
