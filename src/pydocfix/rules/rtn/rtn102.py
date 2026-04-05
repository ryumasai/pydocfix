"""Rule RTN102 - Return type not in docstring or signature."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleReturn, NumPyReturns

from pydocfix.rules._base import BaseRule, DiagnoseContext, Diagnostic


class RTN102(BaseRule):
    """Return type not specified in either docstring or signature."""

    code = "RTN102"
    message = "Return type not in docstring or signature."
    target_kinds = frozenset({
        GoogleReturn,
        NumPyReturns,
    })

    def diagnose(self, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = ctx.target_cst
        if not isinstance(cst_node, (GoogleReturn, NumPyReturns)):
            return
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        ret_type_token = cst_node.return_type
        if ret_type_token is not None and ret_type_token.text.strip():
            return  # has type in docstring

        func = ctx.parent_ast
        if func.returns is not None:  # type: ignore[union-attr]
            return  # has type in signature

        yield self._make_diagnostic(ctx, self.message, target=cst_node)
