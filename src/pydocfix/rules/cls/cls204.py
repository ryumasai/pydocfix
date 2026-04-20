"""Rule CLS204 - __init__ docstring has a Raises section (style='class')."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleSection, NumPySection

from pydocfix.diagnostics import Applicability, Diagnostic
from pydocfix.rules._base import ActivationCondition, FunctionCtx, make_diagnostic, rule
from pydocfix.rules.cls.helpers import is_raises_section
from pydocfix.rules.helpers import delete_section_fix


@rule(
    "CLS204",
    targets=FunctionCtx,
    cst_types=(GoogleSection, NumPySection),
    enabled_by_default=False,
    activation_condition=ActivationCondition("class_docstring_style", frozenset({"class"})),
)
def cls204(node: GoogleSection | NumPySection, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """__init__ docstring has a Raises section but class_docstring_style is 'class'."""
    if ctx.config is None or ctx.config.class_docstring_style != "class":
        return
    if ctx.parent.name != "__init__":
        return
    if not is_raises_section(node):
        return

    fix = delete_section_fix(ctx.docstring_text, node, Applicability.UNSAFE)
    yield make_diagnostic(
        "CLS204",
        ctx,
        "__init__ docstring should not have a Raises section when class_docstring_style is 'class'.",
        fix=fix,
        target=node,
    )
