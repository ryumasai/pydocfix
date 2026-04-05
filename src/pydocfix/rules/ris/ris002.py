"""Rule RIS002 - Docstring has Raises section but function has no raise statements."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleSection, NumPySection

from pydocfix.rules._base import Applicability, BaseRule, DiagnoseContext, Diagnostic, Fix, delete_range
from pydocfix.rules.ris._helpers import get_raised_exceptions, is_raises_section


class RIS002(BaseRule):
    """Docstring has a Raises section but function body has no raise statements."""

    code = "RIS002"
    message = "Unnecessary Raises section in docstring."
    target_kinds = frozenset({
        GoogleSection,
        NumPySection,
    })

    def diagnose(self, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        section = ctx.target_cst
        if not isinstance(section, (GoogleSection, NumPySection)):
            return
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        if not is_raises_section(section):
            return

        raised = get_raised_exceptions(ctx.parent_ast)
        if raised:
            return

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
