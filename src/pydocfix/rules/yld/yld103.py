"""Rule YLD103 - Yield has no type in docstring."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleYield, NumPyYields

from pydocfix.models import ActivationCondition, Applicability, Diagnostic, Edit, Fix
from pydocfix.rules._base import BaseRule, DiagnoseContext
from pydocfix.rules.yld._helpers import get_yield_type


class YLD103(BaseRule[GoogleYield | NumPyYields]):
    """Docstring yield entry has no type (type_annotation_style = "docstring")."""

    code = "YLD103"
    enabled_by_default = False
    conflicts_with = frozenset({"YLD104"})
    activation_condition = ActivationCondition("type_annotation_style", frozenset({"docstring", "both"}))

    def diagnose(self, node: GoogleYield | NumPyYields, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = node
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

        yield self._make_diagnostic(ctx, "Yield has no type in docstring.", fix=fix, target=cst_node)
