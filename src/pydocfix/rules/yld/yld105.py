"""Rule YLD105 - Yield type has no annotation in function signature."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleYield, NumPyYields

from pydocfix.rules._base import BaseRule, ConfigRequirement, DiagnoseContext, Diagnostic
from pydocfix.rules.yld._helpers import get_yield_type


class YLD105(BaseRule):
    """Documented yield has no type annotation in the function signature."""

    code = "YLD105"
    message = "Yield has no type annotation in signature."
    enabled_by_default = False
    conflicts_with = frozenset({"YLD102"})
    requires_config = ConfigRequirement("type_annotation_style", frozenset({"both"}))
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

        if get_yield_type(ctx.parent_ast) is not None:
            return  # has annotation in signature

        yield self._make_diagnostic(ctx, self.message, target=cst_node)
