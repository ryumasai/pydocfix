"""Rule RIS003 - Raises entry has no description."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleException, NumPyException

from pydocfix.rules._base import BaseRule, DiagnoseContext, Diagnostic


class RIS003(BaseRule[GoogleException | NumPyException]):
    """Raises entry has no description."""

    code = "RIS003"

    def diagnose(self, node: GoogleException | NumPyException, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = node
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        desc = cst_node.description
        if desc is not None and desc.text.strip():
            return

        type_token = cst_node.type
        yield self._make_diagnostic(ctx, "Raises entry has no description.", target=type_token or cst_node)
