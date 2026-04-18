"""Rule YLD101 - Docstring yield type does not match signature type."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleYield, NumPyYields

from pydocfix._edits import replace_token
from pydocfix._types import Applicability, Diagnostic, Fix
from pydocfix.rules._base import BaseRule, DiagnoseContext
from pydocfix.rules._type_helpers import normalize_optional
from pydocfix.rules.yld._helpers import get_yield_type


class YLD101(BaseRule[GoogleYield | NumPyYields]):
    """Docstring yield type does not match type hint."""

    code = "YLD101"

    def diagnose(self, node: GoogleYield | NumPyYields, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = node
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        ret_type_token = cst_node.return_type
        if ret_type_token is None:
            return

        hint_type = get_yield_type(ctx.parent_ast)
        if hint_type is None:
            return

        doc_type = ret_type_token.text
        cmp_hint = hint_type
        cmp_doc = doc_type
        if self.config is not None and self.config.allow_optional_shorthand:
            cmp_hint = normalize_optional(hint_type)
            cmp_doc = normalize_optional(doc_type)
        if cmp_doc == cmp_hint:
            return

        fix = Fix(
            edits=[replace_token(ret_type_token, hint_type)],
            applicability=Applicability.UNSAFE,
        )
        message = f"Docstring yield type '{doc_type}' does not match type hint '{hint_type}'."
        yield self._make_diagnostic(ctx, message, fix=fix, target=ret_type_token)
