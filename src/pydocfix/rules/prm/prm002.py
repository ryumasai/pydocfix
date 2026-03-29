"""Rule PRM002 - Function has no parameters but docstring has Args/Parameters section."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import (
    GoogleSection,
    GoogleSectionKind,
    NumPySection,
    NumPySectionKind,
)

from pydocfix.rules._base import Applicability, BaseRule, DiagnoseContext, Diagnostic, Fix, delete_range


class PRM002(BaseRule):
    """Function has no parameters but docstring has an Args/Parameters section."""

    code = "PDX-PRM002"
    message = "Function has no parameters but docstring has Args/Parameters section."
    target_kinds = {
        GoogleSection,
        NumPySection,
    }

    @staticmethod
    def _is_param_section(section: GoogleSection | NumPySection) -> bool:
        if isinstance(section, GoogleSection):
            return section.section_kind == GoogleSectionKind.ARGS
        return section.section_kind == NumPySectionKind.PARAMETERS

    @staticmethod
    def _has_real_params(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """Return True if the function has any parameters besides self/cls."""
        all_positional = [*func.args.posonlyargs, *func.args.args]
        skip_first = bool(all_positional) and all_positional[0].arg in ("self", "cls")
        real_count = len(all_positional) - (1 if skip_first else 0)
        real_count += len(func.args.kwonlyargs)
        if func.args.vararg:
            real_count += 1
        if func.args.kwarg:
            real_count += 1
        return real_count > 0

    def diagnose(self, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        section = ctx.target_cst
        if not isinstance(section, (GoogleSection, NumPySection)):
            return
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return
        if not self._is_param_section(section):
            return
        if self._has_real_params(ctx.parent_ast):
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
