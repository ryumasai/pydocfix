"""Rule CLS001 - __init__ has its own docstring but the class also has one."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.diagnostics import Diagnostic
from pydocfix.rules._base import BaseRule, DiagnoseContext


class CLS001(BaseRule[GoogleDocstring | NumPyDocstring | PlainDocstring]):
    """__init__ has its own docstring but the class also has a docstring."""

    code = "CLS001"

    def diagnose(
        self, node: GoogleDocstring | NumPyDocstring | PlainDocstring, ctx: DiagnoseContext
    ) -> Iterator[Diagnostic]:
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return
        if ctx.parent_ast.name != "__init__":
            return
        if ctx.class_ast is None:
            return
        if ast.get_docstring(ctx.class_ast, clean=False) is None:
            return

        summary_token = node.summary
        yield self._make_diagnostic(
            ctx,
            "__init__ has its own docstring but the class also has a docstring.",
            fix=None,
            target=summary_token or node,
        )
