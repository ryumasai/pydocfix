"""Rule CLS001 - __init__ has its own docstring but the class also has one."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.diagnostics import Diagnostic
from pydocfix.rules._base import FunctionCtx, make_diagnostic, rule


@rule("CLS001", targets=FunctionCtx, cst_types=(GoogleDocstring, NumPyDocstring, PlainDocstring))
def cls001(node: GoogleDocstring | NumPyDocstring | PlainDocstring, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """__init__ has its own docstring but the class also has a docstring."""
    if ctx.parent.name != "__init__":
        return
    if ctx.class_ast is None:
        return
    if ast.get_docstring(ctx.class_ast, clean=False) is None:
        return

    summary_token = node.summary
    yield make_diagnostic(
        "CLS001",
        ctx,
        "__init__ has its own docstring but the class also has a docstring.",
        fix=None,
        target=summary_token or node,
    )
