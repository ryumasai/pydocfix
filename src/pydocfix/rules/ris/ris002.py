"""Rule RIS002 - Docstring has Raises section but function has no raise statements."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleSection, NumPySection

from pydocfix.diagnostics import Applicability, Diagnostic
from pydocfix.rules._base import BaseRule, DiagnoseContext
from pydocfix.rules.helpers import delete_section_fix
from pydocfix.rules.ris.helpers import get_raised_exceptions, is_raises_section


class RIS002(BaseRule[GoogleSection | NumPySection]):
    """Docstring has a Raises section but function body has no raise statements."""

    code = "RIS002"

    def diagnose(self, node: GoogleSection | NumPySection, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        section = node
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        if not is_raises_section(section):
            return

        raised = get_raised_exceptions(ctx.parent_ast)
        if raised:
            return

        # Delete the entire Raises section
        fix = delete_section_fix(ctx.docstring_text, section, Applicability.SAFE)

        header_name = section.header_name
        yield self._make_diagnostic(
            ctx, "Unnecessary Raises section in docstring.", fix=fix, target=header_name or section
        )
