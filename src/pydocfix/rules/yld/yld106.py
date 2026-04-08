"""Rule YLD106 - Yield type has an annotation in function signature (docstring style)."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleYield, NumPyYields

from pydocfix.rules._base import BaseRule, ConfigRequirement, DiagnoseContext, Diagnostic
from pydocfix.rules.yld._helpers import get_yield_type


class YLD106(BaseRule):
    """Documented yield has a type annotation in the function signature (types belong in docstring)."""

    code = "YLD106"
    message = "Yield has a type annotation in signature; types belong in the docstring."
    enabled_by_default = False
    conflicts_with = frozenset({"YLD105"})
    requires_config = ConfigRequirement("type_annotation_style", frozenset({"docstring"}))
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

        if get_yield_type(ctx.parent_ast) is None:
            return  # no annotation in signature — nothing to flag

        yield self._make_diagnostic(ctx, self.message, target=cst_node)
