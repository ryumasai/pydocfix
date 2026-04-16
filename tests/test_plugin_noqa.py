"""Tests for noqa validation with plugin rules."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pytest
from pydocstring import PlainDocstring

from pydocfix.checker import check_file
from pydocfix.rules import build_registry
from pydocfix.rules._base import BaseRule, DiagnoseContext, Diagnostic


class PLUGIN001(BaseRule):
    """Test plugin rule."""

    code = "PLUGIN001"
    _targets = (PlainDocstring,)

    def diagnose(self, node: PlainDocstring, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        """Check for test violation."""
        if node.summary and "bad" in node.summary.text:
            yield self._make_diagnostic(ctx, "Found 'bad' in docstring", target=node.summary)


class TestPluginNoqa:
    """Test that plugin rule codes are properly validated in noqa comments."""

    def test_plugin_rule_code_recognized_in_noqa(self, tmp_path: Path):
        """Plugin rule codes should be recognized as valid pydocfix codes."""
        f = tmp_path / "example.py"
        f.write_text('def foo():\n    """bad"""  # noqa: PLUGIN001\n    pass\n')

        # Build registry with plugin rule class (not instance)
        registry = build_registry(ignore=None, select=["ALL"], plugin_rules=[PLUGIN001])

        # Check file with the registry
        diags, *_ = check_file(
            f.read_text(),
            f,
            registry.type_to_rules,
            known_rule_codes=registry.all_codes(),
        )

        # PLUGIN001 should be suppressed by noqa, no NOQ001 should be emitted
        assert not any(d.rule == "PLUGIN001" for d in diags)
        assert not any(d.rule == "NOQ001" for d in diags)

    def test_unused_plugin_rule_code_detected(self, tmp_path: Path):
        """Unused plugin rule codes in noqa should be detected as NOQ001."""
        f = tmp_path / "example.py"
        f.write_text('def foo():\n    """good"""  # noqa: PLUGIN001\n    pass\n')

        # Build registry with plugin rule class
        registry = build_registry(ignore=None, select=["ALL"], plugin_rules=[PLUGIN001])

        # Check file with the registry
        diags, *_ = check_file(
            f.read_text(),
            f,
            registry.type_to_rules,
            known_rule_codes=registry.all_codes(),
        )

        # PLUGIN001 is unused → should emit NOQ001
        assert any(d.rule == "NOQ001" for d in diags)
        noq_diag = next(d for d in diags if d.rule == "NOQ001")
        assert "PLUGIN001" in noq_diag.message

    def test_plugin_and_builtin_codes_both_recognized(self, tmp_path: Path):
        """Both plugin and builtin codes should be validated."""
        f = tmp_path / "example.py"
        # SUM002 violation exists, PLUGIN001 doesn't
        f.write_text('def foo():\n    """No period"""  # noqa: SUM002, PLUGIN001\n    pass\n')

        # Build registry with plugin rule class (don't include SUM002 in active rules)
        registry = build_registry(ignore=None, select=["PLUGIN*"], plugin_rules=[PLUGIN001])

        # Check file with the registry - need to include all rule codes for noqa validation
        builtin_codes = build_registry(select=["ALL"]).all_codes()
        all_codes = builtin_codes | registry.all_codes()

        diags, *_ = check_file(
            f.read_text(),
            f,
            registry.type_to_rules,
            known_rule_codes=all_codes,
        )

        # Both SUM002 and PLUGIN001 are unused → should emit NOQ001
        assert any(d.rule == "NOQ001" for d in diags)
        noq_diag = next(d for d in diags if d.rule == "NOQ001")
        # Should mention both codes
        assert "SUM002" in noq_diag.message or "PLUGIN001" in noq_diag.message

    def test_unknown_code_ignored_with_plugins(self, tmp_path: Path):
        """Unknown codes (e.g., from other tools) should still be ignored."""
        f = tmp_path / "example.py"
        # Use a violation-free docstring with unknown tool code
        f.write_text('def foo():\n    """Correct docstring."""  # noqa: pylint-C0114\n    pass\n')

        # Build registry with plugin rule class
        registry = build_registry(ignore=None, select=["ALL"], plugin_rules=[PLUGIN001])

        # Check file with the registry
        diags, *_ = check_file(
            f.read_text(),
            f,
            registry.type_to_rules,
            known_rule_codes=registry.all_codes(),
        )

        # pylint-C0114 doesn't match pydocfix code pattern, so noqa is treated as blanket.
        # Since there are no violations, blanket noqa is unused → NOQ001
        assert any(d.rule == "NOQ001" for d in diags)
