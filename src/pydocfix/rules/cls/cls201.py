"""Rule CLS201 - __init__ docstring has a Returns section."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleSection, NumPySection

from pydocfix.diagnostics import Applicability, Diagnostic
from pydocfix.rules._base import FunctionCtx, make_diagnostic, rule
from pydocfix.rules.cls.helpers import is_returns_section
from pydocfix.rules.helpers import delete_section_fix


@rule("CLS201", targets=FunctionCtx, cst_types=(GoogleSection, NumPySection))
def cls201(node: GoogleSection | NumPySection, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """__init__ docstring contains a Returns section."""
    if ctx.parent.name != "__init__":
        return
    if not is_returns_section(node):
        return

    fix = delete_section_fix(ctx.docstring_text, node, Applicability.SAFE)
    yield make_diagnostic(
        "CLS201",
        ctx,
        "__init__ docstring should not have a Returns section.",
        fix=fix,
        target=node,
    )
