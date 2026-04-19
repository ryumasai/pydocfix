"""Rule YLD003 - Yields section has no description."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleYield, NumPyYields

from pydocfix.diagnostics import Diagnostic
from pydocfix.rules._base import BaseRule, DiagnoseContext


class YLD003(BaseRule[GoogleYield | NumPyYields]):
    """Yields section entry has no description."""

    code = "YLD003"

    def diagnose(self, node: GoogleYield | NumPyYields, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = node
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        desc = cst_node.description
        if desc is not None and desc.text.strip():
            return

        ret_type = cst_node.return_type
        yield self._make_diagnostic(ctx, "Yields section has no description.", target=ret_type or cst_node)
