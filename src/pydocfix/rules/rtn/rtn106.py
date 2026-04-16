"""Rule RTN106 - Return type has an annotation in function signature (docstring style)."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleReturn, NumPyReturns

from pydocfix.rules._base import ActivationCondition, BaseRule, DiagnoseContext, Diagnostic


class RTN106(BaseRule[GoogleReturn | NumPyReturns]):
    """Documented return has a type annotation in the function signature (types belong in docstring)."""

    code = "RTN106"
    enabled_by_default = False
    conflicts_with = frozenset({"RTN105"})
    activation_condition = ActivationCondition("type_annotation_style", frozenset({"docstring"}))

    def diagnose(self, node: GoogleReturn | NumPyReturns, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = node
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        func = ctx.parent_ast
        if func.returns is None:  # type: ignore[union-attr]
            return  # no annotation in signature — nothing to flag

        yield self._make_diagnostic(
            ctx, "Return has a type annotation in signature; types belong in the docstring.", target=cst_node
        )
