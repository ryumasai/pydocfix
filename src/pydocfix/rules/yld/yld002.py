"""Rule YLD002 - Non-generator function has Yields section."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleSection, NumPySection

from pydocfix._types import Applicability, Diagnostic
from pydocfix.rules._base import BaseRule, DiagnoseContext
from pydocfix.rules._helpers import delete_section_fix
from pydocfix.rules.yld._helpers import is_generator_function, is_yields_section


class YLD002(BaseRule[GoogleSection | NumPySection]):
    """Function is not a generator but docstring has a Yields section."""

    code = "YLD002"

    def diagnose(self, node: GoogleSection | NumPySection, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        section = node
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        if not is_yields_section(section):
            return

        if is_generator_function(ctx.parent_ast):
            return

        # Delete the entire Yields section
        fix = delete_section_fix(ctx.docstring_text, section, Applicability.SAFE)

        header_name = section.header_name
        yield self._make_diagnostic(
            ctx, "Unnecessary Yields section in docstring.", fix=fix, target=header_name or section
        )
