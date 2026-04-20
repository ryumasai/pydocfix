"""Rule PRM002 - Function has no parameters but docstring has Args/Parameters section."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import (
    GoogleSection,
    NumPySection,
)

from pydocfix.diagnostics import Applicability, Diagnostic
from pydocfix.rules._base import FunctionCtx, make_diagnostic, rule
from pydocfix.rules.helpers import delete_section_fix
from pydocfix.rules.prm.helpers import get_signature_params, is_param_section


@rule("PRM002", targets=FunctionCtx, cst_types=(GoogleSection, NumPySection))
def prm002(node: GoogleSection | NumPySection, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Function has no parameters but docstring has an Args/Parameters section."""
    section = node
    if not is_param_section(section):
        return
    if bool(get_signature_params(ctx.parent)):
        return

    # Delete the entire param section
    fix = delete_section_fix(ctx.docstring_text, section, Applicability.SAFE)

    yield make_diagnostic(
        "PRM002",
        ctx,
        "Function has no parameters but docstring has Args/Parameters section.",
        fix=fix,
        target=section.header_name or section,
    )
