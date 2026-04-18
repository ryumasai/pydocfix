"""Rule RTN101 - Docstring return type does not match type hint."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleReturn, NumPyReturns

from pydocfix.edits import replace_token
from pydocfix.models import Applicability, Diagnostic, Fix
from pydocfix.rules._base import BaseRule, DiagnoseContext
from pydocfix.rules._helpers import normalize_optional


class RTN101(BaseRule[GoogleReturn | NumPyReturns]):
    """Docstring return type does not match type hint."""

    code = "RTN101"

    def _get_return_annotation(self, ast_node: ast.AST) -> str | None:
        if not isinstance(ast_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return None
        if ast_node.returns is None:
            return None
        return ast.unparse(ast_node.returns)

    def diagnose(self, node: GoogleReturn | NumPyReturns, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = node

        ret_type_token = cst_node.return_type
        if ret_type_token is None:
            return

        hint_type = self._get_return_annotation(ctx.parent_ast)
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
        message = f"Docstring return type '{doc_type}' does not match type hint '{hint_type}'."
        yield self._make_diagnostic(ctx, message, fix=fix, target=ret_type_token)
