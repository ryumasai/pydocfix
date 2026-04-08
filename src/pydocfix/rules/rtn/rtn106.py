"""Rule RTN106 - Return type has an annotation in function signature (docstring style)."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleReturn, NumPyReturns

from pydocfix.rules._base import BaseRule, ConfigRequirement, DiagnoseContext, Diagnostic


class RTN106(BaseRule):
    """Documented return has a type annotation in the function signature (types belong in docstring)."""

    code = "RTN106"
    message = "Return has a type annotation in signature; types belong in the docstring."
    enabled_by_default = False
    conflicts_with = frozenset({"RTN105"})
    requires_config = ConfigRequirement("type_annotation_style", frozenset({"docstring"}))
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
        if func.returns is None:  # type: ignore[union-attr]
            return  # no annotation in signature — nothing to flag

        yield self._make_diagnostic(ctx, self.message, target=cst_node)
