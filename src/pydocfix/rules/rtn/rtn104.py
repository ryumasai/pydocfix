"""Rule RTN104 - Return has no type in docstring."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleReturn, NumPyReturns

from pydocfix.rules._base import Applicability, BaseRule, ConfigRequirement, DiagnoseContext, Diagnostic, Edit, Fix


class RTN104(BaseRule):
    """Docstring return entry has no type (type_annotation_style = "docstring")."""

    code = "RTN104"
    message = "Return has no type in docstring."
    enabled_by_default = False
    conflicts_with = frozenset({"RTN103"})
    requires_config = ConfigRequirement("type_annotation_style", frozenset({"docstring", "both"}))
    target_kinds = frozenset(
        {
            GoogleReturn,
            NumPyReturns,
        }
    )

    def diagnose(self, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = ctx.target_cst
        if not isinstance(cst_node, (GoogleReturn, NumPyReturns)):
            return
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        ret_type_token = cst_node.return_type
        if ret_type_token is not None and ret_type_token.text.strip():
            return  # Already has type

        # Try to get type from signature for the fix
        func = ctx.parent_ast
        ann = None
        if func.returns is not None:  # type: ignore[union-attr]
            ann = ast.unparse(func.returns)  # type: ignore[union-attr]

        fix = None
        if ann:
            if isinstance(cst_node, GoogleReturn):
                fix = Fix(
                    edits=[Edit(start=cst_node.range.start, end=cst_node.range.start, new_text=f"{ann}: ")],
                    applicability=Applicability.UNSAFE,
                )
            else:  # NumPyReturns
                fix = Fix(
                    edits=[Edit(start=cst_node.range.start, end=cst_node.range.start, new_text=f"{ann}\n")],
                    applicability=Applicability.UNSAFE,
                )

        yield self._make_diagnostic(ctx, self.message, fix=fix, target=cst_node)
