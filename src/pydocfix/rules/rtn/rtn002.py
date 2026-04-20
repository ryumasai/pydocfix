"""Rule RTN002 - Function has no return type but docstring has Returns section."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import (
    GoogleSection,
    NumPySection,
)

from pydocfix.diagnostics import Applicability, Diagnostic
from pydocfix.rules._base import FunctionCtx, make_diagnostic, rule
from pydocfix.rules.helpers import delete_section_fix
from pydocfix.rules.rtn.helpers import is_returns_section, returns_a_value


@rule("RTN002", targets=FunctionCtx, cst_types=(GoogleSection, NumPySection))
def rtn002(node: GoogleSection | NumPySection, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Returns section present but the function does not return a value."""
    section = node

    if not is_returns_section(section):
        return

    if returns_a_value(ctx.parent):
        return

    # Delete the entire Returns section
    fix = delete_section_fix(ctx.docstring_text, section, Applicability.SAFE)

    header_name = section.header_name
    yield make_diagnostic(
        "RTN002", ctx, "Unnecessary Returns section in docstring.", fix=fix, target=header_name or section
    )
