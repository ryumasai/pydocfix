"""Rule YLD003 - Yields section has no description."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleYield, NumPyYields

from pydocfix.rules._base import BaseRule, DiagnoseContext, Diagnostic


class YLD003(BaseRule):
    """Yields section entry has no description."""

    code = "YLD003"
    message = "Yields section has no description."
    target_kinds = {
        GoogleYield,
        NumPyYields,
    }

    def diagnose(self, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = ctx.target_cst
        if not isinstance(cst_node, (GoogleYield, NumPyYields)):
            return
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        desc = cst_node.description
        if desc is not None and desc.text.strip():
            return

        ret_type = cst_node.return_type
        yield self._make_diagnostic(ctx, self.message, target=ret_type or cst_node)
