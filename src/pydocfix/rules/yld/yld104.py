"""Rule YLD104 - Yield has no type in docstring."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleYield, NumPyYields

from pydocfix.rules._base import Applicability, BaseRule, DiagnoseContext, Diagnostic, Edit, Fix
from pydocfix.rules.yld._helpers import get_yield_type


class YLD104(BaseRule):
    """Docstring yield entry has no type (type_annotation_style = "docstring")."""

    code = "YLD104"
    message = "Yield has no type in docstring."
    enabled_by_default = False
    conflicts_with = frozenset({"YLD103"})
    requires_config = ("type_annotation_style", "docstring")
    target_kinds = {
        GoogleYield,
        NumPyYields,
    }

    def diagnose(self, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = ctx.target_cst
        if not isinstance(cst_node, (GoogleYield, NumPyYields)):
            return
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        ret_type_token = cst_node.return_type
        if ret_type_token is not None and ret_type_token.text.strip():
            return

        ann = get_yield_type(ctx.parent_ast)
        fix = None
        if ann:
            if isinstance(cst_node, GoogleYield):
                fix = Fix(
                    edits=[Edit(start=cst_node.range.start, end=cst_node.range.start, new_text=f"{ann}: ")],
                    applicability=Applicability.UNSAFE,
                )
            else:  # NumPyYields
                fix = Fix(
                    edits=[Edit(start=cst_node.range.start, end=cst_node.range.start, new_text=f"{ann}\n")],
                    applicability=Applicability.UNSAFE,
                )

        yield self._make_diagnostic(ctx, self.message, fix=fix, target=cst_node)
