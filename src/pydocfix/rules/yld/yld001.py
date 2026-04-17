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

from pydocfix.rules._base import (
    Applicability,
    BaseRule,
    DiagnoseContext,
    Diagnostic,
    Fix,
    detect_section_indent,
    section_append_edit,
)
from pydocfix.rules._helpers import build_section_stub, detect_docstring_style, has_section
from pydocfix.rules.yld._helpers import get_yield_type, is_generator_function


class YLD001(BaseRule[GoogleDocstring | NumPyDocstring | PlainDocstring]):
    """Generator function has no Yields section in docstring."""

    code = "YLD001"

    def diagnose(
        self, node: GoogleDocstring | NumPyDocstring | PlainDocstring, ctx: DiagnoseContext
    ) -> Iterator[Diagnostic]:
        root = node
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return
        if isinstance(root, PlainDocstring) and (self.config is None or self.config.skip_short_docstrings):
            return  # summary-only docstring — skip per skip_short_docstrings
        if not is_generator_function(ctx.parent_ast):
            return
        if has_section(root, GoogleSectionKind.YIELDS, NumPySectionKind.YIELDS):
            return

        style = detect_docstring_style(root, self.config)
        yield_type = get_yield_type(ctx.parent_ast)
        section_indent = detect_section_indent(ctx.docstring_text, ctx.docstring_stmt.col_offset)

        # Build stub with optional yield type
        entries = [yield_type] if yield_type else None
        stub = build_section_stub("yields", style, section_indent, entries)

        fix = Fix(
            edits=[section_append_edit(ctx.docstring_text, root.range.end, stub)],
            applicability=Applicability.UNSAFE,
        )
        summary_token = root.summary
        yield self._make_diagnostic(ctx, "Missing Yields section in docstring.", fix=fix, target=summary_token or root)
