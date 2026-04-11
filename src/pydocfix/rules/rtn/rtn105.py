"""Rule RTN105 - Return type has no annotation in function signature."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleReturn, NumPyReturns

from pydocfix.rules._base import BaseRule, ConfigRequirement, DiagnoseContext, Diagnostic


class RTN105(BaseRule):
    """Documented return has no type annotation in the function signature."""

    code = "RTN105"
    message = "Return has no type annotation in signature."
    enabled_by_default = False
    conflicts_with = frozenset({"RTN102", "RTN106"})
    requires_config = ConfigRequirement("type_annotation_style", frozenset({"signature", "both"}))
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

        func = ctx.parent_ast
        if func.returns is not None:  # type: ignore[union-attr]
            return  # has annotation in signature

        yield self._make_diagnostic(ctx, self.message, target=cst_node)
