"""Rule YLD001 - Generator function has no Yields section."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import (
    GoogleDocstring,
    GoogleSectionKind,
    NumPyDocstring,
    NumPySectionKind,
    PlainDocstring,
)

from pydocfix.rules._base import Applicability, BaseRule, DiagnoseContext, Diagnostic, Fix, insert_at
from pydocfix.rules.yld._helpers import get_yield_type, is_generator_function


class YLD001(BaseRule):
    """Generator function has no Yields section in docstring."""

    code = "PDX-YLD001"
    message = "Missing Yields section in docstring."
    target_kinds = {
        GoogleDocstring,
        NumPyDocstring,
        PlainDocstring,
    }

    @staticmethod
    def _has_yields_section(root) -> bool:
        if isinstance(root, PlainDocstring):
            return False
        for sec in root.sections:
            if isinstance(root, GoogleDocstring):
                if sec.section_kind == GoogleSectionKind.YIELDS:
                    return True
            else:
                if sec.section_kind == NumPySectionKind.YIELDS:
                    return True
        return False

    def diagnose(self, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        root = ctx.target_cst
        if not isinstance(root, (GoogleDocstring, NumPyDocstring, PlainDocstring)):
            return
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return
        if not is_generator_function(ctx.parent_ast):
            return
        if self._has_yields_section(root):
            return

        is_numpy = isinstance(root, NumPyDocstring)
        yield_type = get_yield_type(ctx.parent_ast)
        if is_numpy:
            stub = f"\n\nYields\n------\n{yield_type}\n" if yield_type else "\n\nYields\n------\n"
        else:
            stub = f"\n\nYields:\n    {yield_type}:\n" if yield_type else "\n\nYields:\n"

        fix = Fix(
            edits=[insert_at(root.range.end, stub)],
            applicability=Applicability.UNSAFE,
        )
        summary_token = root.summary
        yield self._make_diagnostic(ctx, self.message, fix=fix, target=summary_token or root)
