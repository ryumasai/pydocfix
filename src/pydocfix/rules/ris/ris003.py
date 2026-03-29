"""Rule RIS003 - Raises entry has no description."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleException, NumPyException

from pydocfix.rules._base import BaseRule, DiagnoseContext, Diagnostic


class RIS003(BaseRule):
    """Raises entry has no description."""

    code = "PDX-RIS003"
    message = "Raises entry has no description."
    target_kinds = {
        GoogleException,
        NumPyException,
    }

    def diagnose(self, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = ctx.target_cst
        if not isinstance(cst_node, (GoogleException, NumPyException)):
            return
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        desc = cst_node.description
        if desc is not None and desc.text.strip():
            return

        type_token = cst_node.type
        yield self._make_diagnostic(ctx, self.message, target=type_token or cst_node)
