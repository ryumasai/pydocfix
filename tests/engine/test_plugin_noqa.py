"""Tests for noqa interaction with plugin rules."""

from __future__ import annotations

from pathlib import Path

from pydocfix.checker import check_file
from pydocfix.config import Config
from tests.engine.synthetic_rules.plugnoqa001 import PLUGNOQA001
from tests.helpers import make_type_to_rules


class TestPluginNoqa:
    """Tests for noqa suppression with plugin rules."""

    def test_inline_noqa_suppresses_plugin(self, load_test_fixture):
        """Inline noqa suppresses plugin rule violation."""
        source = load_test_fixture("foo_docstring_noqa_plugnoqa001.py").read_text(encoding="utf-8")
        config = Config(skip_short_docstrings=False)
        rules = make_type_to_rules(PLUGNOQA001(config))
        diagnostics, _, _ = check_file(
            source,
            Path("test.py"),
            rules,
            config=config,
            known_rule_codes=frozenset({"PLUGNOQA001"}),
        )

        assert not any(d.rule == "PLUGNOQA001" for d in diagnostics)

    def test_blanket_noqa_suppresses_plugin(self, load_test_fixture):
        """Blanket noqa suppresses all violations including plugin."""
        source = load_test_fixture("foo_docstring_blanket_noqa.py").read_text(encoding="utf-8")
        config = Config(skip_short_docstrings=False)
        rules = make_type_to_rules(PLUGNOQA001(config))
        diagnostics, _, _ = check_file(
            source,
            Path("test.py"),
            rules,
            config=config,
        )

        assert not any(d.rule == "PLUGNOQA001" for d in diagnostics)

    def test_specific_noqa_does_not_suppress_other_rule(self, load_test_fixture):
        """Specific noqa code only suppresses that code."""
        from pydocfix.rules.sum.sum002 import SUM002

        source = load_test_fixture("foo_no_period_noqa_plugnoqa001.py").read_text(encoding="utf-8")
        config = Config(skip_short_docstrings=False)
        rules = make_type_to_rules(PLUGNOQA001(config), SUM002(config))
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
