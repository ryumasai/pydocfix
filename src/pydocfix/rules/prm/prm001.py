"""Rule PRM001 - Function has parameters but docstring has no Args/Parameters section."""

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
from pydocfix.rules.prm.helpers import get_signature_params


class PRM001(BaseRule[GoogleDocstring | NumPyDocstring | PlainDocstring]):
    """Function has parameters but docstring has no Args/Parameters section."""

    code = "PRM001"

    def diagnose(
        self, node: GoogleDocstring | NumPyDocstring | PlainDocstring, ctx: DiagnoseContext
    ) -> Iterator[Diagnostic]:
        root = node
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        sig_params = get_signature_params(ctx.parent_ast)
        if not sig_params:
            return
        if isinstance(root, PlainDocstring) and (self.config is None or self.config.skip_short_docstrings):
            return  # summary-only docstring — skip per skip_short_docstrings
        if not isinstance(root, PlainDocstring) and has_section(
            root, GoogleSectionKind.ARGS, NumPySectionKind.PARAMETERS
        ):
            return

        style = detect_docstring_style(root, self.config)
        section_indent = detect_section_indent(ctx.docstring_text, ctx.docstring_stmt.col_offset)
        stub = build_section_stub("args", style, section_indent, sig_params)

        fix = Fix(
            edits=[section_append_edit(ctx.docstring_text, root.range.end, stub)],
            applicability=Applicability.UNSAFE,
        )
        summary_token = root.summary
        yield self._make_diagnostic(
            ctx, "Missing Args/Parameters section in docstring.", fix=fix, target=summary_token or root
        )
