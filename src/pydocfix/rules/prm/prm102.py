"""Rule PRM102 - Parameter has no type in docstring or signature."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleArg, NumPyParameter

from pydocfix.rules._base import BaseRule, DiagnoseContext, Diagnostic


class PRM102(BaseRule):
    """Parameter has no type annotation in either docstring or signature."""

    code = "PDX-PRM102"
    message = "Parameter has no type in docstring or signature."
    target_kinds = {
        GoogleArg,
        NumPyParameter,
    }

    @staticmethod
    def _get_annotation_map(func: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, str]:
        result: dict[str, str] = {}
        for arg in (*func.args.args, *func.args.posonlyargs, *func.args.kwonlyargs):
            if arg.annotation is not None:
                result[arg.arg] = ast.unparse(arg.annotation)
        if func.args.vararg and func.args.vararg.annotation is not None:
            result[func.args.vararg.arg] = ast.unparse(func.args.vararg.annotation)
        if func.args.kwarg and func.args.kwarg.annotation is not None:
            result[func.args.kwarg.arg] = ast.unparse(func.args.kwarg.annotation)
        return result

    def diagnose(self, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = ctx.target_cst
        if not isinstance(cst_node, (GoogleArg, NumPyParameter)):
            return
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        if isinstance(cst_node, GoogleArg):
            name_token = cst_node.name
            type_token = cst_node.type
        else:
            name_token = cst_node.names[0] if cst_node.names else None
            type_token = cst_node.type
        if name_token is None:
            return

        if type_token is not None and type_token.text.strip():
            return  # has type in docstring

        bare_name = name_token.text.lstrip("*")
        ann_map = self._get_annotation_map(ctx.parent_ast)
        if bare_name in ann_map:
            return  # has type in signature

        message = f"Parameter \'{name_token.text}\' has no type in docstring or signature."
        yield self._make_diagnostic(ctx, message, target=name_token)
