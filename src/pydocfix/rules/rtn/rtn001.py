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

from pydocfix.edits import detect_section_indent, section_append_edit
from pydocfix.models import Applicability, Diagnostic, Fix
from pydocfix.rules._base import BaseRule, DiagnoseContext
from pydocfix.rules._helpers import build_section_stub, detect_docstring_style, has_section
from pydocfix.rules.rtn._helpers import has_return_annotation


class RTN001(BaseRule[GoogleDocstring | NumPyDocstring | PlainDocstring]):
    """Function has return type annotation but docstring has no Returns section."""

    code = "RTN001"

    def diagnose(
        self, node: GoogleDocstring | NumPyDocstring | PlainDocstring, ctx: DiagnoseContext
    ) -> Iterator[Diagnostic]:
        root = node
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return
        if isinstance(root, PlainDocstring) and (self.config is None or self.config.skip_short_docstrings):
            return  # summary-only docstring — skip per skip_short_docstrings
        if not has_return_annotation(ctx.parent_ast):
            return
        if has_section(root, GoogleSectionKind.RETURNS, NumPySectionKind.RETURNS):
            return

        style = detect_docstring_style(root, self.config)
        ret_ann = ast.unparse(ctx.parent_ast.returns)  # type: ignore[union-attr]
        section_indent = detect_section_indent(ctx.docstring_text, ctx.docstring_stmt.col_offset)

        stub = build_section_stub("returns", style, section_indent, [ret_ann])

        fix = Fix(
            edits=[section_append_edit(ctx.docstring_text, root.range.end, stub)],
            applicability=Applicability.UNSAFE,
        )
        summary_token = root.summary
        yield self._make_diagnostic(ctx, "Missing Returns section in docstring.", fix=fix, target=summary_token or root)
