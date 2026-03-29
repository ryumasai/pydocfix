"""Rule YLD101 - Docstring yield type does not match signature type."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleYield, NumPyYields

from pydocfix.rules._base import Applicability, BaseRule, DiagnoseContext, Diagnostic, Fix, replace_token
from pydocfix.rules.yld._helpers import get_yield_type


class YLD101(BaseRule):
    """Docstring yield type does not match type hint."""

    code = "PDX-YLD101"
    message = "Docstring yield type does not match type hint."
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

        ret_type_token = cst_node.return_type
        if ret_type_token is None:
            return

        hint_type = get_yield_type(ctx.parent_ast)
        if hint_type is None:
            return

        doc_type = ret_type_token.text
        if doc_type == hint_type:
            return

        fix = Fix(
            edits=[replace_token(ret_type_token, hint_type)],
            applicability=Applicability.UNSAFE,
        )
        message = f"Docstring yield type \'{doc_type}\' does not match type hint \'{hint_type}\'."
        yield self._make_diagnostic(ctx, message, fix=fix, target=ret_type_token)
