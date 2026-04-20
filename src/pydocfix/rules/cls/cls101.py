"""Rule CLS101 - Class docstring has a Returns section."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleSection, NumPySection

from pydocfix.diagnostics import Applicability, Diagnostic
from pydocfix.rules._base import ClassCtx, make_diagnostic, rule
from pydocfix.rules.cls.helpers import is_returns_section
from pydocfix.rules.helpers import delete_section_fix


@rule("CLS101", targets=ClassCtx, cst_types=(GoogleSection, NumPySection))
def cls101(node: GoogleSection | NumPySection, ctx: ClassCtx) -> Iterator[Diagnostic]:
    """Class docstring contains a Returns section."""
    if not is_returns_section(node):
        return

    fix = delete_section_fix(ctx.docstring_text, node, Applicability.SAFE)
    yield make_diagnostic(
        "CLS101",
        ctx,
        "Class docstring should not have a Returns section.",
        fix=fix,
        target=node,
    )
