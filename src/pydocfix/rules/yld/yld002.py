"""Rule YLD002 - Non-generator function has Yields section."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleSection, NumPySection

from pydocfix.diagnostics import Applicability, Diagnostic
from pydocfix.rules._base import FunctionCtx, make_diagnostic, rule
from pydocfix.rules.helpers import delete_section_fix
from pydocfix.rules.yld.helpers import is_generator_function, is_yields_section


@rule("YLD002", ctx_types=frozenset({FunctionCtx}), cst_types=frozenset({GoogleSection, NumPySection}))
def yld002(node: GoogleSection | NumPySection, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Function is not a generator but docstring has a Yields section."""
    section = node

    if not is_yields_section(section):
        return

    if is_generator_function(ctx.parent):
        return

    # Delete the entire Yields section
    fix = delete_section_fix(ctx.docstring_text, section, Applicability.SAFE)

    header_name = section.header_name
    yield make_diagnostic(
        "YLD002", ctx, "Unnecessary Yields section in docstring.", fix=fix, target=header_name or section
    )
