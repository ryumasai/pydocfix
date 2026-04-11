"""Rule YLD104 - Redundant yield type in docstring when signature has annotation."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleYield, NumPyYields

from pydocfix.rules._base import (
    Applicability,
    BaseRule,
    ConfigRequirement,
    DiagnoseContext,
    Diagnostic,
    Fix,
    delete_range,
)
from pydocfix.rules.yld._helpers import get_yield_type


class YLD104(BaseRule):
    """Signature has yield type annotation but docstring also specifies type (redundant)."""

    code = "YLD104"
    message = "Redundant yield type in docstring; type annotation exists in signature."
    enabled_by_default = False
    conflicts_with = frozenset({"YLD103"})
    requires_config = ConfigRequirement("type_annotation_style", frozenset({"signature"}))
    target_kinds = frozenset(
        {
            GoogleYield,
            NumPyYields,
        }
    )

    def diagnose(self, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = ctx.target_cst
        if not isinstance(cst_node, (GoogleYield, NumPyYields)):
            return
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        ret_type_token = cst_node.return_type
        if ret_type_token is None:
            return

        if get_yield_type(ctx.parent_ast) is None:
            return

        colon_token = cst_node.colon
        ds_bytes = ctx.docstring_text.encode("utf-8")

        if isinstance(cst_node, GoogleYield) and colon_token:
            end = colon_token.range.end
            if end < len(ds_bytes) and ds_bytes[end : end + 1] == b" ":
                end += 1
            fix = Fix(
                edits=[delete_range(ret_type_token.range.start, end)],
                applicability=Applicability.SAFE,
            )
        elif isinstance(cst_node, NumPyYields):
            nl_after = ds_bytes.find(b"\n", ret_type_token.range.end)
            end = nl_after + 1 if nl_after != -1 else ret_type_token.range.end
            fix = Fix(
                edits=[delete_range(ret_type_token.range.start, end)],
                applicability=Applicability.SAFE,
            )
        else:
            fix = Fix(edits=[], applicability=Applicability.SAFE)

        yield self._make_diagnostic(ctx, self.message, fix=fix, target=ret_type_token)
