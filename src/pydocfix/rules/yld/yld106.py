"""Rule YLD106 - Yield type has an annotation in function signature (docstring style)."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleYield, NumPyYields

from pydocfix.diagnostics import Diagnostic
from pydocfix.rules._base import ActivationCondition, BaseRule, DiagnoseContext
from pydocfix.rules.yld.helpers import get_yield_type


class YLD106(BaseRule[GoogleYield | NumPyYields]):
    """Documented yield has a type annotation in the function signature (types belong in docstring)."""

    code = "YLD106"
    enabled_by_default = False
    conflicts_with = frozenset({"YLD105"})
    activation_condition = ActivationCondition("type_annotation_style", frozenset({"docstring"}))

    def diagnose(self, node: GoogleYield | NumPyYields, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = node
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        if get_yield_type(ctx.parent_ast) is None:
            return  # no annotation in signature — nothing to flag

        yield self._make_diagnostic(
            ctx, "Yield has a type annotation in signature; types belong in the docstring.", target=cst_node
        )
