"""Tests for plugin integration with the checker."""

from __future__ import annotations

from pathlib import Path

from pydocfix.checker import check_file
from pydocfix.config import Config
from tests.engine.synthetic_rules.testplugin001 import TESTPLUGIN001
from tests.helpers import make_type_to_rules


class TestPluginIntegration:
    """Tests for plugin rules integrated with check_file."""

    def test_plugin_rule_detects_violation(self, load_test_fixture):
        """Plugin rule can detect violations."""
        source = load_test_fixture("foo_hi_short.py").read_text(encoding="utf-8")
        config = Config(skip_short_docstrings=False)
        rules = make_type_to_rules(TESTPLUGIN001(config))
        diagnostics, _, _ = check_file(source, Path("test.py"), rules, config=config)

        assert any(d.rule == "TESTPLUGIN001" for d in diagnostics)

    def test_plugin_rule_no_violation(self, load_test_fixture):
        """Plugin rule does not flag longer docstrings."""
        source = load_test_fixture("foo_long_docstring.py").read_text(encoding="utf-8")
        config = Config(skip_short_docstrings=False)
        rules = make_type_to_rules(TESTPLUGIN001(config))
        diagnostics, _, _ = check_file(source, Path("test.py"), rules, config=config)

        assert not any(d.rule == "TESTPLUGIN001" for d in diagnostics)

    def test_plugin_and_builtin_together(self, load_test_fixture):
        """Plugin rules work alongside built-in rules."""
        from pydocfix.rules.sum.sum002 import SUM002

        source = load_test_fixture("foo_hi_no_period.py").read_text(encoding="utf-8")
        config = Config(skip_short_docstrings=False)
        rules = make_type_to_rules(TESTPLUGIN001(config), SUM002(config))
        diagnostics, _, _ = check_file(source, Path("test.py"), rules, config=config)

        codes = {d.rule for d in diagnostics}
        assert "SUM002" in codes
        assert "TESTPLUGIN001" in codes
