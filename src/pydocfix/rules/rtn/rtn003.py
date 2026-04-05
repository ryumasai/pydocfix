"""Rule RTN003 - Returns section has no description."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleReturn, NumPyReturns

from pydocfix.rules._base import BaseRule, DiagnoseContext, Diagnostic


class RTN003(BaseRule):
    """Returns section entry has no description."""

    code = "RTN003"
    message = "Returns section has no description."
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

        desc = cst_node.description
        if desc is not None and desc.text.strip():
            return

        ret_type = cst_node.return_type
        yield self._make_diagnostic(ctx, self.message, target=ret_type or cst_node)
