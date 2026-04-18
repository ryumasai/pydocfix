"""Rule PRM009 - Docstring parameter name missing '*' or '**' prefix."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleArg, NumPyParameter

from pydocfix._edits import replace_token
from pydocfix._types import Applicability, Diagnostic, Fix
from pydocfix.rules._base import BaseRule, DiagnoseContext
from pydocfix.rules.prm._helpers import get_param_name_token


class PRM009(BaseRule[GoogleArg | NumPyParameter]):
    """Docstring parameter name missing '*' or '**' prefix."""

    code = "PRM009"

    def _get_vararg_kwarg_names(self, ast_node: ast.AST) -> dict[str, str]:
        """Return mapping of bare name -> prefixed name for *args/**kwargs."""
        if not isinstance(ast_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return {}
        result: dict[str, str] = {}
        if ast_node.args.vararg:
            result[ast_node.args.vararg.arg] = f"*{ast_node.args.vararg.arg}"
        if ast_node.args.kwarg:
            result[ast_node.args.kwarg.arg] = f"**{ast_node.args.kwarg.arg}"
        return result

    def diagnose(self, node: GoogleArg | NumPyParameter, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = node

        name_token = get_param_name_token(cst_node)
        if name_token is None:
            return

        param_name = name_token.text
        if param_name.startswith("*"):
            return

        prefixed_names = self._get_vararg_kwarg_names(ctx.parent_ast)
        expected = prefixed_names.get(param_name)
        if expected is None:
            return

        fix = Fix(
            edits=[replace_token(name_token, expected)],
            applicability=Applicability.SAFE,
        )
        message = f"Docstring parameter '{param_name}' should be '{expected}'."
        yield self._make_diagnostic(ctx, message, fix=fix, target=name_token)
