"""Rule RTN101 - Docstring return type does not match type hint."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleReturn, NumPyReturns

from pydocfix.diagnostics import Applicability, Diagnostic, Fix
from pydocfix.fixes import replace_token
from pydocfix.rules._base import FunctionCtx, make_diagnostic, rule
from pydocfix.rules.helpers import normalize_optional


def _get_return_annotation(func: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    if func.returns is None:
        return None
    return ast.unparse(func.returns)


@rule("RTN101", ctx_types=frozenset({FunctionCtx}), cst_types=frozenset({GoogleReturn, NumPyReturns}))
def rtn101(node: GoogleReturn | NumPyReturns, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Docstring return type does not match type hint."""
    cst_node = node

    ret_type_token = cst_node.return_type
    if ret_type_token is None:
        return

    hint_type = _get_return_annotation(ctx.parent)
    if hint_type is None:
        return

    doc_type = ret_type_token.text
    cmp_hint = hint_type
    cmp_doc = doc_type
    if ctx.config is not None and ctx.config.allow_optional_shorthand:
        cmp_hint = normalize_optional(hint_type)
        cmp_doc = normalize_optional(doc_type)
    if cmp_doc == cmp_hint:
        return

    fix = Fix(
        edits=[replace_token(ret_type_token, hint_type)],
        applicability=Applicability.UNSAFE,
    )
    message = f"Docstring return type '{doc_type}' does not match type hint '{hint_type}'."
    yield make_diagnostic("RTN101", ctx, message, fix=fix, target=ret_type_token)
