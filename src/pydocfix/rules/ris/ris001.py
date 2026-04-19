"""Rule RIS001 - Function raises exceptions but docstring has no Raises section."""

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

from pydocfix.diagnostics import Applicability, Diagnostic, Fix
from pydocfix.fixes import section_append_edit
from pydocfix.rules._base import BaseRule, DiagnoseContext
from pydocfix.rules.helpers import build_section_stub, detect_docstring_style, detect_section_indent, has_section
from pydocfix.rules.ris.helpers import get_raised_exceptions


class RIS001(BaseRule[GoogleDocstring | NumPyDocstring | PlainDocstring]):
    """Function has raise statements but docstring has no Raises section."""

    code = "RIS001"

    def diagnose(
        self, node: GoogleDocstring | NumPyDocstring | PlainDocstring, ctx: DiagnoseContext
    ) -> Iterator[Diagnostic]:
        root = node
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return
        if isinstance(root, PlainDocstring) and (self.config is None or self.config.skip_short_docstrings):
            return  # summary-only docstring — skip per skip_short_docstrings

        raised = get_raised_exceptions(ctx.parent_ast)
        if not raised:
            return

        if has_section(root, GoogleSectionKind.RAISES, NumPySectionKind.RAISES):
            return

        style = detect_docstring_style(root, self.config)
        section_indent = detect_section_indent(ctx.docstring_text, ctx.docstring_stmt.col_offset)

        stub = build_section_stub("raises", style, section_indent, raised)

        fix = Fix(
            edits=[section_append_edit(ctx.docstring_text, root.range.end, stub)],
            applicability=Applicability.UNSAFE,
        )
        summary_token = root.summary
        yield self._make_diagnostic(ctx, "Missing Raises section in docstring.", fix=fix, target=summary_token or root)
