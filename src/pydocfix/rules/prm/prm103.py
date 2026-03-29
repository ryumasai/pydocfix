"""Rule PRM103 - Redundant type in docstring when signature has type annotation."""

from __future__ import annotations

import ast
from collections.abc import Iterator
from typing import TYPE_CHECKING

from pydocstring import GoogleArg, NumPyParameter

from pydocfix.rules._base import Applicability, BaseRule, DiagnoseContext, Diagnostic, Fix, delete_range

if TYPE_CHECKING:
    pass


class PRM103(BaseRule):
    """Signature has type annotation but docstring also specifies type (redundant)."""

    code = "PDX-PRM103"
    message = "Redundant type in docstring; type annotation exists in signature."
    enabled_by_default = False
    target_kinds = {
        GoogleArg,
        NumPyParameter,
    }

    @staticmethod
    def _has_annotation(func: ast.FunctionDef | ast.AsyncFunctionDef, bare_name: str) -> bool:
        for arg in (*func.args.args, *func.args.posonlyargs, *func.args.kwonlyargs):
            if arg.arg == bare_name and arg.annotation is not None:
                return True
        if func.args.vararg and func.args.vararg.arg == bare_name and func.args.vararg.annotation is not None:
            return True
        return bool(func.args.kwarg and func.args.kwarg.arg == bare_name and func.args.kwarg.annotation is not None)

    def _build_delete_type_fix(self, cst_node, ds_text: str) -> Fix:
        """Build a fix that removes the type annotation from the docstring entry."""
        ds_bytes = ds_text.encode("utf-8")
        if isinstance(cst_node, GoogleArg):
            # Delete from open_bracket to close_bracket (inclusive)
            if cst_node.open_bracket and cst_node.close_bracket:
                start = cst_node.open_bracket.range.start
                if start > 0 and ds_bytes[start - 1 : start] == b" ":
                    start -= 1
                return Fix(
                    edits=[delete_range(start, cst_node.close_bracket.range.end)],
                    applicability=Applicability.SAFE,
                )
        else:  # NumPyParameter
            if cst_node.type and cst_node.colon:
                return Fix(
                    edits=[delete_range(cst_node.colon.range.start, cst_node.type.range.end)],
                    applicability=Applicability.SAFE,
                )
        return Fix(edits=[], applicability=Applicability.SAFE)

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
        if name_token is None or type_token is None:
            return

        bare_name = name_token.text.lstrip("*")
        if not self._has_annotation(ctx.parent_ast, bare_name):
            return

        fix = self._build_delete_type_fix(cst_node, ctx.docstring_text)
        message = f"Parameter '{name_token.text}' has redundant type in docstring."
        yield self._make_diagnostic(ctx, message, fix=fix, target=type_token)
