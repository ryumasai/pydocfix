"""Rule RIS004 - Exception raised in function body missing from Raises section."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleSection, NumPySection

from pydocfix.edits import detect_section_indent
from pydocfix.models import Applicability, Diagnostic, Edit, Fix
from pydocfix.rules._base import BaseRule, DiagnoseContext
from pydocfix.rules.ris._helpers import (
    _bare_exc_name,
    get_docstring_exception_names,
    get_raised_exceptions,
    is_raises_section,
)


class RIS004(BaseRule[GoogleSection | NumPySection]):
    """Raised exception not documented in the Raises section."""

    code = "RIS004"

    @staticmethod
    def _detect_entry_indent(ds_text: str, section, stmt_col_offset: int = 0) -> str:
        """Derive indentation of exception entries from existing entries."""
        section_indent = detect_section_indent(ds_text, stmt_col_offset)
        return section_indent + "    "

    @staticmethod
    def _build_entry(exc_name: str, *, is_numpy: bool, indent: str) -> str:
        if is_numpy:
            return f"\n{indent}{exc_name}"
        return f"\n{indent}{exc_name}:"

    def diagnose(self, node: GoogleSection | NumPySection, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        section = node
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        if not is_raises_section(section):
            return

        documented = set(get_docstring_exception_names(ctx.docstring_cst, section))
        raised = [_bare_exc_name(e) for e in get_raised_exceptions(ctx.parent_ast)]

        is_numpy = isinstance(section, NumPySection)
        indent = self._detect_entry_indent(ctx.docstring_text, section, ctx.docstring_stmt.col_offset)
        header_name = section.header_name

        for exc_name in raised:
            if exc_name in documented:
                continue

            entry = self._build_entry(exc_name, is_numpy=is_numpy, indent=indent)
            fix = Fix(
                edits=[Edit(start=section.range.end, end=section.range.end, new_text=entry)],
                applicability=Applicability.UNSAFE,
            )
            message = f"Raised exception '{exc_name}' not documented in Raises section."
            yield self._make_diagnostic(ctx, message, fix=fix, target=header_name or section)
