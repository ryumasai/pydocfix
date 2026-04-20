"""Example custom rules for pydocfix.

This module demonstrates how to create custom linting rules as pydocfix plugins.
"""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.rules import (
    Applicability,
    Diagnostic,
    Fix,
    insert_at,
)
from pydocfix.rules._base import BaseCtx, ClassCtx, FunctionCtx, ModuleCtx, make_diagnostic, rule


@rule(
    "EXAMPLE001",
    targets=(FunctionCtx, ClassCtx, ModuleCtx),
    cst_types=(GoogleDocstring, NumPyDocstring, PlainDocstring),
)
def example001(node: GoogleDocstring | NumPyDocstring | PlainDocstring, ctx: BaseCtx) -> Iterator[Diagnostic]:
    """Example rule: Check for minimum docstring length.

    This rule enforces that docstrings have a minimum length to ensure
    adequate documentation.

    Supports plugin-config:

    .. code-block:: toml

        [tool.pydocfix.plugin-config.example001]
        min-length = 10  # default: 10
    """
    if node.summary is None:
        return

    summary_text = node.summary.text.strip()
    plugin_cfg = ctx.config.plugin_config.get("example001", {}) if ctx.config else {}
    min_length: int = int(plugin_cfg.get("min-length", 10))

    if len(summary_text) < min_length:
        yield make_diagnostic(
            "EXAMPLE001",
            ctx,
            f"Docstring summary is too short ({len(summary_text)} chars, minimum {min_length})",
            target=node.summary,
        )


@rule("EXAMPLE002", targets=FunctionCtx, cst_types=(GoogleDocstring, NumPyDocstring), enabled_by_default=False)
def example002(node: GoogleDocstring | NumPyDocstring, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Example rule: Require Examples section for public functions.

    This rule enforces that public functions (not starting with _) have
    an Examples section in their docstring.
    """
    # Only check function docstrings
    if not isinstance(ctx.parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return

    # Skip private functions
    if ctx.parent.name.startswith("_"):
        return

    # Check for Examples section
    has_examples = False
    for section in node.sections:
        section_name = section.header_name.text.lower().strip()
        if "example" in section_name:
            has_examples = True
            break

    if not has_examples:
        yield make_diagnostic(
            "EXAMPLE002",
            ctx,
            f"Public function '{ctx.parent.name}' should have an Examples section",
            target=node,
        )


@rule("EXAMPLE003", targets=FunctionCtx, cst_types=GoogleDocstring, enabled_by_default=False)
def example003(node: GoogleDocstring, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Example rule with auto-fix: Add TODO marker for incomplete docstrings."""
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

        yield make_diagnostic(
            "EXAMPLE003",
            ctx,
            "Docstring appears incomplete. Consider adding a TODO marker.",
            fix=fix,
            target=node.summary,
        )


__all__ = [
    "example001",
    "example002",
    "example003",
]
