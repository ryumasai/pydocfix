"""Rule RTN002 - Function has no return type but docstring has Returns section."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import (
    GoogleSection,
    NumPySection,
)

from pydocfix.rules._base import Applicability, BaseRule, DiagnoseContext, Diagnostic, Fix, delete_range
from pydocfix.rules.rtn._helpers import has_return_annotation, is_returns_section


class RTN002(BaseRule):
    """Function has no return type annotation but docstring has a Returns section."""

    code = "PDX-RTN002"
    message = "Unnecessary Returns section in docstring."
    target_kinds = {
        GoogleSection,
        NumPySection,
    }

    def diagnose(self, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        section = ctx.target_cst
        if not isinstance(section, (GoogleSection, NumPySection)):
            return
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        if not is_returns_section(section):
            return

        if has_return_annotation(ctx.parent_ast):
            return

        # Delete the entire Returns section
        ds_bytes = ctx.docstring_text.encode("utf-8")
        nl_before = ds_bytes.rfind(b"\n", 0, section.range.start)
        start = nl_before if nl_before != -1 else section.range.start
        nl_after = ds_bytes.find(b"\n", section.range.end)
        end = nl_after + 1 if nl_after != -1 else section.range.end

        fix = Fix(
            edits=[delete_range(start, end)],
            applicability=Applicability.SAFE,
        )
        header_name = section.header_name
        yield self._make_diagnostic(ctx, self.message, fix=fix, target=header_name or section)
