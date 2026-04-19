"""Rule PRM003 - Docstring documents ``self`` or ``cls``."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleArg, NumPyParameter

from pydocfix.diagnostics import Applicability, Diagnostic
from pydocfix.rules._base import BaseRule, DiagnoseContext
from pydocfix.rules._helpers import delete_entry_fix
from pydocfix.rules.prm._helpers import get_param_name_token


class PRM003(BaseRule[GoogleArg | NumPyParameter]):
    """Docstring should not document ``self`` or ``cls``."""

    code = "PRM003"

    def diagnose(self, node: GoogleArg | NumPyParameter, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = node
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        name_token = get_param_name_token(cst_node)
        if name_token is None:
            return

        if name_token.text not in ("self", "cls"):
            return

        fix = delete_entry_fix(ctx.docstring_text, cst_node.range, Applicability.SAFE)
        message = f"Docstring should not document '{name_token.text}'."
        yield self._make_diagnostic(ctx, message, fix=fix, target=name_token)
