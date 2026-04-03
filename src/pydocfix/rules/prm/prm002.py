"""Rule PRM002 - Function has no parameters but docstring has Args/Parameters section."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import (
    GoogleSection,
    NumPySection,
)

from pydocfix.rules._base import Applicability, BaseRule, DiagnoseContext, Diagnostic, Fix, delete_range
from pydocfix.rules.prm._helpers import get_signature_params, is_param_section


class PRM002(BaseRule):
    """Function has no parameters but docstring has an Args/Parameters section."""

    code = "PRM002"
    message = "Function has no parameters but docstring has Args/Parameters section."
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
        if not is_param_section(section):
            return
        if bool(get_signature_params(ctx.parent_ast)):
            return

        # Delete the entire param section
        ds_bytes = ctx.docstring_text.encode("utf-8")
        nl_before = ds_bytes.rfind(b"\n", 0, section.range.start)
        start = nl_before if nl_before != -1 else section.range.start
        nl_after = ds_bytes.find(b"\n", section.range.end)
        end = nl_after + 1 if nl_after != -1 else section.range.end

        fix = Fix(
            edits=[delete_range(start, end)],
            applicability=Applicability.SAFE,
        )
        yield self._make_diagnostic(ctx, self.message, fix=fix, target=section.header_name or section)
