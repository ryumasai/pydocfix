"""Rule RTN104 - Redundant return type in docstring when signature has annotation."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleReturn, NumPyReturns

from pydocfix._edits import delete_range
from pydocfix._types import ActivationCondition, Applicability, Diagnostic, Fix
from pydocfix.rules._base import BaseRule, DiagnoseContext


class RTN104(BaseRule[GoogleReturn | NumPyReturns]):
    """Signature has return type annotation but docstring also specifies type (redundant)."""

    code = "RTN104"
    enabled_by_default = False
    conflicts_with = frozenset({"RTN103"})
    activation_condition = ActivationCondition("type_annotation_style", frozenset({"signature"}))

    def diagnose(self, node: GoogleReturn | NumPyReturns, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = node
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        ret_type_token = cst_node.return_type
        if ret_type_token is None:
            return  # No type in docstring — nothing to flag

        func = ctx.parent_ast
        if func.returns is None:  # type: ignore[union-attr]
            return  # No return annotation in signature — not redundant

        colon_token = cst_node.colon
        ds_bytes = ctx.docstring_text.encode("utf-8")

        if isinstance(cst_node, GoogleReturn) and colon_token:
            end = colon_token.range.end
            if end < len(ds_bytes) and ds_bytes[end : end + 1] == b" ":
                end += 1
            fix = Fix(
                edits=[delete_range(ret_type_token.range.start, end)],
                applicability=Applicability.SAFE,
            )
        elif isinstance(cst_node, NumPyReturns):
            nl_after = ds_bytes.find(b"\n", ret_type_token.range.end)
            end = nl_after + 1 if nl_after != -1 else ret_type_token.range.end
            fix = Fix(
                edits=[delete_range(ret_type_token.range.start, end)],
                applicability=Applicability.SAFE,
            )
        else:
            fix = Fix(edits=[], applicability=Applicability.SAFE)

        yield self._make_diagnostic(
            ctx,
            "Redundant return type in docstring; type annotation exists in signature.",
            fix=fix,
            target=ret_type_token,
        )
