"""Example custom rules for pydocfix.

This module demonstrates how to create custom linting rules as pydocfix plugins.
"""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.rules import (
    Applicability,
    BaseRule,
    DiagnoseContext,
    Diagnostic,
    Fix,
    insert_at,
)


class EXAMPLE001(BaseRule[GoogleDocstring | NumPyDocstring | PlainDocstring]):
    """Example rule: Check for minimum docstring length.

    This rule enforces that docstrings have a minimum length to ensure
    adequate documentation.

    Supports plugin-config:

    .. code-block:: toml

        [tool.pydocfix.plugin-config.example001]
        min-length = 10  # default: 10
    """

    code = "EXAMPLE001"
    enabled_by_default = True

    def diagnose(
        self, node: GoogleDocstring | NumPyDocstring | PlainDocstring, ctx: DiagnoseContext
    ) -> Iterator[Diagnostic]:
        """Check if the docstring summary is too short."""
        if node.summary is None:
            return

        summary_text = node.summary.text.strip()
        plugin_cfg = self.config.plugin_config.get("example001", {}) if self.config else {}
        min_length: int = int(plugin_cfg.get("min-length", 10))

        if len(summary_text) < min_length:
            yield self._make_diagnostic(
                ctx,
                f"Docstring summary is too short ({len(summary_text)} chars, minimum {min_length})",
                target=node.summary,
            )


class EXAMPLE002(BaseRule[GoogleDocstring | NumPyDocstring]):
    """Example rule: Require Examples section for public functions.

    This rule enforces that public functions (not starting with _) have
    an Examples section in their docstring.
    """

    code = "EXAMPLE002"
    enabled_by_default = False  # Opt-in rule

    def diagnose(self, node: GoogleDocstring | NumPyDocstring, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        """Check if Examples section exists for public functions."""
        # Only check function docstrings
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        # Skip private functions
        if ctx.parent_ast.name.startswith("_"):
            return

        # Check for Examples section
        has_examples = False
        for section in node.sections:
            section_name = section.header_name.text.lower().strip()
            if "example" in section_name:
                has_examples = True
                break

        if not has_examples:
            yield self._make_diagnostic(
                ctx,
                f"Public function '{ctx.parent_ast.name}' should have an Examples section",
                target=node,
            )


class EXAMPLE003(BaseRule[GoogleDocstring]):
    """Example rule with auto-fix: Add TODO marker for incomplete docstrings."""

    code = "EXAMPLE003"
    enabled_by_default = False

    def diagnose(self, node: GoogleDocstring, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        """Add TODO marker if docstring seems incomplete."""
        if node.summary is None:
            return

        summary_text = node.summary.text.strip().lower()
        incomplete_markers = ["todo", "fixme", "tbd", "...", "placeholder"]

        # Check if already marked as incomplete
        has_marker = any(marker in summary_text for marker in incomplete_markers)

        # Check if it looks incomplete (very short or generic)
        generic_phrases = ["function", "method", "class", "this is a"]
        looks_incomplete = len(summary_text) < 20 or any(phrase in summary_text for phrase in generic_phrases)

        if looks_incomplete and not has_marker:
            # Suggest adding a TODO marker
            fix = Fix(
                edits=[insert_at(node.summary.range.start, "TODO: ")],
                applicability=Applicability.SAFE,
            )

            yield self._make_diagnostic(
                ctx,
                "Docstring appears incomplete. Consider adding a TODO marker.",
                fix=fix,
                target=node.summary,
            )


__all__ = [
    "EXAMPLE001",
    "EXAMPLE002",
    "EXAMPLE003",
]
