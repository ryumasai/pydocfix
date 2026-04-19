"""Rule RTN002 - Function has no return type but docstring has Returns section."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import (
    GoogleSection,
    NumPySection,
)

from pydocfix.diagnostics import Applicability, Diagnostic
from pydocfix.rules._base import BaseRule, DiagnoseContext
from pydocfix.rules._helpers import delete_section_fix
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
        fix = delete_section_fix(ctx.docstring_text, section, Applicability.SAFE)

        header_name = section.header_name
        yield self._make_diagnostic(
            ctx, "Unnecessary Returns section in docstring.", fix=fix, target=header_name or section
        )
