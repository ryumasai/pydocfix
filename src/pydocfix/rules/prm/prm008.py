"""Rule PRM008 - Docstring parameter has empty description."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleArg, NumPyParameter

from pydocfix.diagnostics import Diagnostic
from pydocfix.rules._base import BaseRule, DiagnoseContext
from pydocfix.rules.prm.helpers import get_param_name_token


class PRM008(BaseRule[GoogleArg | NumPyParameter]):
    """Docstring parameter has no description."""

    code = "PRM008"

    def diagnose(self, node: GoogleArg | NumPyParameter, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = node
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        name_token = get_param_name_token(cst_node)
        if name_token is None:
            return

        desc = cst_node.description
        if desc is not None and desc.text.strip():
            return

        message = f"Parameter '{name_token.text}' has no description."
        yield self._make_diagnostic(ctx, message, target=name_token)
