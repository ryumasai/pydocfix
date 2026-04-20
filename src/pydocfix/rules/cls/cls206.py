"""Rule CLS206 - __init__ docstring missing Raises section (style='init')."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleDocstring, GoogleSectionKind, NumPyDocstring, NumPySectionKind, PlainDocstring

from pydocfix.diagnostics import Applicability, Diagnostic, Fix
from pydocfix.fixes import section_append_edit
from pydocfix.rules._base import ActivationCondition, BaseRule, DiagnoseContext
from pydocfix.rules.helpers import build_section_stub, detect_docstring_style, detect_section_indent, has_section
from pydocfix.rules.ris.helpers import get_raised_exceptions


class CLS206(BaseRule[GoogleDocstring | NumPyDocstring | PlainDocstring]):
    """__init__ docstring is missing a Raises section but class_docstring_style is 'init'."""

    code = "CLS206"
    enabled_by_default = False
    activation_condition = ActivationCondition("class_docstring_style", frozenset({"init"}))

    def diagnose(
        self, node: GoogleDocstring | NumPyDocstring | PlainDocstring, ctx: DiagnoseContext
    ) -> Iterator[Diagnostic]:
        if self.config is None or self.config.class_docstring_style != "init":
            return
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return
        if ctx.parent_ast.name != "__init__":
            return

        root = node
        if isinstance(root, PlainDocstring) and (self.config is None or self.config.skip_short_docstrings):
            return

        raised = get_raised_exceptions(ctx.parent_ast)
        if not raised:
            return

        if not isinstance(root, PlainDocstring) and has_section(
            root, GoogleSectionKind.RAISES, NumPySectionKind.RAISES
        ):
            return

        style = detect_docstring_style(root, self.config)
        section_indent = detect_section_indent(ctx.docstring_text, ctx.docstring_stmt.col_offset)
        stub = build_section_stub("raises", style, section_indent, raised)

        fix = Fix(
            edits=[section_append_edit(ctx.docstring_text, root.range.end, stub)],
            applicability=Applicability.UNSAFE,
        )
        summary_token = root.summary
        yield self._make_diagnostic(
            ctx,
            "__init__ docstring is missing a Raises section (class_docstring_style is 'init').",
            fix=fix,
            target=summary_token or root,
        )
