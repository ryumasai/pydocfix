"""Rule YLD001 - Generator function has no Yields section."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import (
    GoogleDocstring,
    GoogleSectionKind,
    NumPyDocstring,
    NumPySectionKind,
    PlainDocstring,
)

from pydocfix.diagnostics import Applicability, Diagnostic, Fix
from pydocfix.fixes import section_append_edit
from pydocfix.rules._base import FunctionCtx, make_diagnostic, rule
from pydocfix.rules.helpers import build_section_stub, detect_docstring_style, detect_section_indent, has_section
from pydocfix.rules.yld.helpers import get_yield_type, is_generator_function


@rule("YLD001", ctx_types=frozenset({FunctionCtx}), cst_types=frozenset({GoogleDocstring, NumPyDocstring, PlainDocstring}))
def yld001(node: GoogleDocstring | NumPyDocstring | PlainDocstring, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Generator function has no Yields section in docstring."""
    root = node
    if isinstance(root, PlainDocstring) and (ctx.config is None or ctx.config.skip_short_docstrings):
        return  # summary-only docstring — skip per skip_short_docstrings
    if not is_generator_function(ctx.parent):
        return
    if has_section(root, GoogleSectionKind.YIELDS, NumPySectionKind.YIELDS):
        return

    style = detect_docstring_style(root, ctx.config)
    yield_type = get_yield_type(ctx.parent)
    section_indent = detect_section_indent(ctx.docstring_text, ctx.docstring_stmt.col_offset)

    # Build stub with optional yield type
    entries = [yield_type] if yield_type else None
    stub = build_section_stub("yields", style, section_indent, entries)

    fix = Fix(
        edits=[section_append_edit(ctx.docstring_text, root.range.end, stub)],
        applicability=Applicability.UNSAFE,
    )
    summary_token = root.summary
    yield make_diagnostic("YLD001", ctx, "Missing Yields section in docstring.", fix=fix, target=summary_token or root)
