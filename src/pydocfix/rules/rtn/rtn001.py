"""Rule RTN001 - Function has return type annotation but no Returns section."""

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


class RTN001(BaseRule):
    """Function has return type annotation but docstring has no Returns section."""

    code = "PDX-RTN001"
    message = "Missing Returns section in docstring."
    target_kinds = {
        GoogleDocstring,
        NumPyDocstring,
        PlainDocstring,
    }

    @staticmethod
    def _has_return_annotation(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        if func.returns is None:
            return False
        if isinstance(func.returns, ast.Constant) and func.returns.value is None:
            return False
        ann = ast.unparse(func.returns)
        return ann not in ("None",)

    @staticmethod
    def _has_returns_section(root) -> bool:
        if isinstance(root, PlainDocstring):
            return False
        for sec in root.sections:
            if isinstance(root, GoogleDocstring):
                if sec.section_kind == GoogleSectionKind.RETURNS:
                    return True
            else:
                if sec.section_kind == NumPySectionKind.RETURNS:
                    return True
        return False

    def diagnose(self, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        root = ctx.target_cst
        if not isinstance(root, (GoogleDocstring, NumPyDocstring, PlainDocstring)):
            return
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return
        if not self._has_return_annotation(ctx.parent_ast):
            return
        if self._has_returns_section(root):
            return

        is_numpy = isinstance(root, NumPyDocstring)
        ret_ann = ast.unparse(ctx.parent_ast.returns)  # type: ignore[union-attr]
        stub = f"\n\nReturns\n-------\n{ret_ann}\n" if is_numpy else f"\n\nReturns:\n    {ret_ann}:\n"

        fix = Fix(
            edits=[insert_at(root.range.end, stub)],
            applicability=Applicability.UNSAFE,
        )
        summary_token = root.summary
        yield self._make_diagnostic(ctx, self.message, fix=fix, target=summary_token or root)
