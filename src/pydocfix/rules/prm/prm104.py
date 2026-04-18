"""Rule PRM104 - Redundant type in docstring when signature has type annotation."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleArg, NumPyParameter

from pydocfix.edits import delete_range
from pydocfix.models import ActivationCondition, Applicability, Diagnostic, Fix
from pydocfix.rules._base import BaseRule, DiagnoseContext
from pydocfix.rules.prm._helpers import bare_name, get_annotation_map, get_param_name_token


class PRM104(BaseRule[GoogleArg | NumPyParameter]):
    """Signature has type annotation but docstring also specifies type (redundant)."""

    code = "PRM104"
    enabled_by_default = False
    conflicts_with = frozenset({"PRM103"})
    activation_condition = ActivationCondition("type_annotation_style", frozenset({"signature"}))

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

    def diagnose(self, node: GoogleArg | NumPyParameter, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = node
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        if isinstance(cst_node, GoogleArg):
            name_token = get_param_name_token(cst_node)
            type_token = cst_node.type
        else:
            name_token = get_param_name_token(cst_node)
            type_token = cst_node.type
        if name_token is None or type_token is None:
            return

        b = bare_name(name_token.text)
        if not get_annotation_map(ctx.parent_ast).get(b):
            return

        fix = self._build_delete_type_fix(cst_node, ctx.docstring_text)
        message = f"Parameter '{name_token.text}' has redundant type in docstring."
        yield self._make_diagnostic(ctx, message, fix=fix, target=type_token)
