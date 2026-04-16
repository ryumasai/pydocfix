"""Rule PRM005 - Docstring has parameter not in function signature."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleArg, NumPyParameter

from pydocfix.rules._base import Applicability, BaseRule, DiagnoseContext, Diagnostic
from pydocfix.rules._helpers import delete_entry_fix
from pydocfix.rules.prm._helpers import bare_name, get_param_name_token


class PRM005(BaseRule[GoogleArg | NumPyParameter]):
    """Docstring documents a parameter that does not exist in the function signature."""

    code = "PRM005"

    @staticmethod
    def _get_signature_names(func: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
        """Return bare parameter names from the function signature (includes self/cls)."""
        names: set[str] = set()
        for arg in (*func.args.posonlyargs, *func.args.args, *func.args.kwonlyargs):
            names.add(arg.arg)
        if func.args.vararg:
            names.add(func.args.vararg.arg)
        if func.args.kwarg:
            names.add(func.args.kwarg.arg)
        return names

    def diagnose(self, node: GoogleArg | NumPyParameter, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = node
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        name_token = get_param_name_token(cst_node)
        if name_token is None:
            return

        sig_names = self._get_signature_names(ctx.parent_ast)
        b = bare_name(name_token.text)
        if b in sig_names:
            return

        fix = delete_entry_fix(ctx.docstring_text, cst_node, Applicability.UNSAFE)
        message = f"Parameter '{name_token.text}' not in function signature."
        yield self._make_diagnostic(ctx, message, fix=fix, target=name_token)
