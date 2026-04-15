"""Rule RTN002 - Function has no return type but docstring has Returns section."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import (
    GoogleSection,
    NumPySection,
)

from pydocfix.rules._base import Applicability, BaseRule, DiagnoseContext, Diagnostic, Fix, delete_range
from pydocfix.rules.rtn._helpers import is_returns_section, returns_a_value


class RTN002(BaseRule[GoogleSection | NumPySection]):
    """Returns section present but the function does not return a value."""

    code = "RTN002"

    def diagnose(self, node: GoogleSection | NumPySection, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        section = node
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        if not is_returns_section(section):
            return

        if returns_a_value(ctx.parent_ast):
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
        yield self._make_diagnostic(ctx, "Unnecessary Returns section in docstring.", fix=fix, target=header_name or section)
