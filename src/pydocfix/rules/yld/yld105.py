"""Rule YLD105 - Yield type has no annotation in function signature."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleYield, NumPyYields

from pydocfix.diagnostics import Diagnostic
from pydocfix.rules._base import ActivationCondition, BaseRule, DiagnoseContext
from pydocfix.rules.yld._helpers import get_yield_type


class YLD105(BaseRule[GoogleYield | NumPyYields]):
    """Documented yield has no type annotation in the function signature."""

    code = "YLD105"
    enabled_by_default = False
    conflicts_with = frozenset({"YLD102", "YLD106"})
    activation_condition = ActivationCondition("type_annotation_style", frozenset({"signature", "both"}))

    def diagnose(self, node: GoogleYield | NumPyYields, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = node
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        if get_yield_type(ctx.parent_ast) is not None:
            return  # has annotation in signature

        yield self._make_diagnostic(ctx, "Yield has no type annotation in signature.", target=cst_node)
