"""Rule RIS001 - Function raises exceptions but docstring has no Raises section."""

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
from pydocfix.rules.ris.helpers import get_raised_exceptions


@rule(
    "RIS001",
    ctx_types=frozenset({FunctionCtx}),
    cst_types=frozenset({GoogleDocstring, NumPyDocstring, PlainDocstring}),
)
def ris001(node: GoogleDocstring | NumPyDocstring | PlainDocstring, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Function has raise statements but docstring has no Raises section."""
    root = node
    # __init__ raises are always handled by CLS rules
    if ctx.parent.name == "__init__":
        return
    if isinstance(root, PlainDocstring) and (ctx.config is None or ctx.config.skip_short_docstrings):
        return  # summary-only docstring — skip per skip_short_docstrings

    raised = get_raised_exceptions(ctx.parent)
    if not raised:
        return

    if has_section(root, GoogleSectionKind.RAISES, NumPySectionKind.RAISES):
        return

    style = detect_docstring_style(root, ctx.config)
    section_indent = detect_section_indent(ctx.docstring_text, ctx.docstring_stmt.col_offset)

    stub = build_section_stub("raises", style, section_indent, raised)

    fix = Fix(
        edits=[section_append_edit(ctx.docstring_text, root.range.end, stub)],
        applicability=Applicability.UNSAFE,
    )
    summary_token = root.summary
    yield make_diagnostic("RIS001", ctx, "Missing Raises section in docstring.", fix=fix, target=summary_token or root)
