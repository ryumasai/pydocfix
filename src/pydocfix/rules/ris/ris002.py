"""Rule RIS002 - Docstring has Raises section but function has no raise statements."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleSection, NumPySection

from pydocfix.diagnostics import Applicability, Diagnostic
from pydocfix.rules._base import FunctionCtx, make_diagnostic, rule
from pydocfix.rules.helpers import delete_section_fix
from pydocfix.rules.ris.helpers import get_raised_exceptions, is_raises_section


@rule("RIS002", ctx_types=frozenset({FunctionCtx}), cst_types=frozenset({GoogleSection, NumPySection}))
def ris002(node: GoogleSection | NumPySection, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Docstring has a Raises section but function body has no raise statements."""
    section = node

    if not is_raises_section(section):
        return

    raised = get_raised_exceptions(ctx.parent)
    if raised:
        return

    # Delete the entire Raises section
    fix = delete_section_fix(ctx.docstring_text, section, Applicability.SAFE)

    header_name = section.header_name
    yield make_diagnostic(
        "RIS002", ctx, "Unnecessary Raises section in docstring.", fix=fix, target=header_name or section
    )
