"""Rule YLD102 - Yield type not in docstring or signature."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleYield, NumPyYields

from pydocfix.models import Diagnostic
from pydocfix.rules._base import BaseRule, DiagnoseContext
from pydocfix.rules.yld._helpers import get_yield_type


class YLD102(BaseRule[GoogleYield | NumPyYields]):
    """Yield type not specified in either docstring or signature."""

    code = "YLD102"

    def diagnose(self, node: GoogleYield | NumPyYields, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = node
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        ret_type_token = cst_node.return_type
        if ret_type_token is not None and ret_type_token.text.strip():
            return

        if get_yield_type(ctx.parent_ast) is not None:
            return

        yield self._make_diagnostic(ctx, "Yield type not in docstring or signature.", target=cst_node)
