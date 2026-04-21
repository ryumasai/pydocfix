"""Rule RTN001 - Function has return type annotation but no Returns section."""

from __future__ import annotations

import ast
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
from pydocfix.rules.rtn.helpers import has_return_annotation


@rule("RTN001", ctx_types=frozenset({FunctionCtx}), cst_types=frozenset({GoogleDocstring, NumPyDocstring, PlainDocstring}))
def rtn001(node: GoogleDocstring | NumPyDocstring | PlainDocstring, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Function has return type annotation but docstring has no Returns section."""
    root = node
    if isinstance(root, PlainDocstring) and (ctx.config is None or ctx.config.skip_short_docstrings):
        return  # summary-only docstring — skip per skip_short_docstrings
    if not has_return_annotation(ctx.parent):
        return
    if has_section(root, GoogleSectionKind.RETURNS, NumPySectionKind.RETURNS):
        return

    style = detect_docstring_style(root, ctx.config)
    ret_ann = ast.unparse(ctx.parent.returns)  # type: ignore[union-attr]
    section_indent = detect_section_indent(ctx.docstring_text, ctx.docstring_stmt.col_offset)

    stub = build_section_stub("returns", style, section_indent, [ret_ann])

    fix = Fix(
        edits=[section_append_edit(ctx.docstring_text, root.range.end, stub)],
        applicability=Applicability.UNSAFE,
    )
    summary_token = root.summary
    yield make_diagnostic("RTN001", ctx, "Missing Returns section in docstring.", fix=fix, target=summary_token or root)
