"""Rule CLS202 - __init__ docstring has a Yields section."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleSection, NumPySection

from pydocfix.diagnostics import Applicability, Diagnostic
from pydocfix.rules._base import FunctionCtx, make_diagnostic, rule
from pydocfix.rules.cls.helpers import is_yields_section
from pydocfix.rules.helpers import delete_section_fix


@rule("CLS202", ctx_types=frozenset({FunctionCtx}), cst_types=frozenset({GoogleSection, NumPySection}))
def cls202(node: GoogleSection | NumPySection, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """__init__ docstring contains a Yields section."""
    if ctx.parent.name != "__init__":
        return
    if not is_yields_section(node):
        return

    fix = delete_section_fix(ctx.docstring_text, node, Applicability.SAFE)
    yield make_diagnostic(
        "CLS202",
        ctx,
        "__init__ docstring should not have a Yields section.",
        fix=fix,
        target=node,
    )
