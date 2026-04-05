"""Rule YLD002 - Non-generator function has Yields section."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleSection, NumPySection

from pydocfix.rules._base import Applicability, BaseRule, DiagnoseContext, Diagnostic, Fix, delete_range
from pydocfix.rules.yld._helpers import is_generator_function, is_yields_section


class YLD002(BaseRule):
    """Function is not a generator but docstring has a Yields section."""

    code = "YLD002"
    message = "Unnecessary Yields section in docstring."
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

        if not is_yields_section(section):
            return

        if is_generator_function(ctx.parent_ast):
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
