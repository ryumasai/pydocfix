"""Rule CLS202 - __init__ docstring has a Yields section."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleSection, NumPySection

from pydocfix.diagnostics import Applicability, Diagnostic
from pydocfix.rules._base import BaseRule, DiagnoseContext
from pydocfix.rules.cls.helpers import is_yields_section
from pydocfix.rules.helpers import delete_section_fix


class CLS202(BaseRule[GoogleSection | NumPySection]):
    """__init__ docstring contains a Yields section."""

    code = "CLS202"

    def diagnose(self, node: GoogleSection | NumPySection, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return
        if ctx.parent_ast.name != "__init__":
            return
        if not is_yields_section(node):
            return

        fix = delete_section_fix(ctx.docstring_text, node, Applicability.SAFE)
        yield self._make_diagnostic(
            ctx,
            "__init__ docstring should not have a Yields section.",
            fix=fix,
            target=node,
        )
