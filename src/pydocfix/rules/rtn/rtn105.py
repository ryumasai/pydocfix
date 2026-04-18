"""Rule RTN105 - Return type has no annotation in function signature."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleReturn, NumPyReturns

from pydocfix._types import ActivationCondition, Diagnostic
from pydocfix.rules._base import BaseRule, DiagnoseContext


class RTN105(BaseRule[GoogleReturn | NumPyReturns]):
    """Documented return has no type annotation in the function signature."""

    code = "RTN105"
    enabled_by_default = False
    conflicts_with = frozenset({"RTN102", "RTN106"})
    activation_condition = ActivationCondition("type_annotation_style", frozenset({"signature", "both"}))

    def diagnose(self, node: GoogleReturn | NumPyReturns, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = node
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        func = ctx.parent_ast
        if func.returns is not None:  # type: ignore[union-attr]
            return  # has annotation in signature

        yield self._make_diagnostic(ctx, "Return has no type annotation in signature.", target=cst_node)
