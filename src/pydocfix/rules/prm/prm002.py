"""Rule PRM002 - Function has no parameters but docstring has Args/Parameters section."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import (
    GoogleSection,
    NumPySection,
)

from pydocfix.rules._base import Applicability, BaseRule, DiagnoseContext, Diagnostic
from pydocfix.rules._helpers import delete_section_fix
from pydocfix.rules.prm._helpers import get_signature_params, is_param_section


class PRM002(BaseRule[GoogleSection | NumPySection]):
    """Function has no parameters but docstring has an Args/Parameters section."""

    code = "PRM002"

    def diagnose(self, node: GoogleSection | NumPySection, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        section = node
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return
        if not is_param_section(section):
            return
        if bool(get_signature_params(ctx.parent_ast)):
            return

        # Delete the entire param section
        fix = delete_section_fix(ctx.docstring_text, section, Applicability.SAFE)

        yield self._make_diagnostic(
            ctx,
            "Function has no parameters but docstring has Args/Parameters section.",
            fix=fix,
            target=section.header_name or section,
        )
