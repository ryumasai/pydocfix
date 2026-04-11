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

from pydocfix.rules._base import (
    Applicability,
    BaseRule,
    DiagnoseContext,
    Diagnostic,
    Fix,
    detect_section_indent,
    section_append_edit,
)
from pydocfix.rules.rtn._helpers import has_return_annotation


class RTN001(BaseRule):
    """Function has return type annotation but docstring has no Returns section."""

    code = "RTN001"
    message = "Missing Returns section in docstring."
    target_kinds = frozenset(
        {
            GoogleDocstring,
            NumPyDocstring,
            PlainDocstring,
        }
    )

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
        if isinstance(root, PlainDocstring):
            if self.config is None or self.config.skip_short_docstrings:
                return  # summary-only docstring — skip per skip_short_docstrings
        if not has_return_annotation(ctx.parent_ast):
            return
        if self._has_returns_section(root):
            return

        is_numpy = isinstance(root, NumPyDocstring)
        ret_ann = ast.unparse(ctx.parent_ast.returns)  # type: ignore[union-attr]
        section_indent = detect_section_indent(ctx.docstring_text, ctx.docstring_stmt.col_offset)
        entry_indent = section_indent + "    "
        if is_numpy:
            stub = f"{section_indent}Returns\n{section_indent}-------\n{section_indent}{ret_ann}"
        else:
            stub = f"{section_indent}Returns:\n{entry_indent}{ret_ann}:"

        fix = Fix(
            edits=[section_append_edit(ctx.docstring_text, root.range.end, stub)],
            applicability=Applicability.UNSAFE,
        )
        summary_token = root.summary
        yield self._make_diagnostic(ctx, self.message, fix=fix, target=summary_token or root)
