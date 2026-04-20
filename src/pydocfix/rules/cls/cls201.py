"""Rule CLS201 - __init__ docstring has a Returns section."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleSection, NumPySection

from pydocfix.diagnostics import Applicability, Diagnostic
from pydocfix.rules._base import BaseRule, DiagnoseContext
from pydocfix.rules.cls.helpers import is_returns_section
from pydocfix.rules.helpers import delete_section_fix


class CLS201(BaseRule[GoogleSection | NumPySection]):
    """__init__ docstring contains a Returns section."""

    code = "CLS201"

    def diagnose(self, node: GoogleSection | NumPySection, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return
        if ctx.parent_ast.name != "__init__":
            return
        if not is_returns_section(node):
            return

        fix = delete_section_fix(ctx.docstring_text, node, Applicability.SAFE)
        yield self._make_diagnostic(
            ctx,
            "__init__ docstring should not have a Returns section.",
            fix=fix,
            target=node,
        )
