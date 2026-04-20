"""Rule CLS203 - __init__ docstring has an Args section (style='class')."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleSection, NumPySection

from pydocfix.diagnostics import Applicability, Diagnostic
from pydocfix.rules._base import ActivationCondition, FunctionCtx, make_diagnostic, rule
from pydocfix.rules.cls.helpers import is_param_section
from pydocfix.rules.helpers import delete_section_fix


@rule(
    "CLS203",
    targets=FunctionCtx,
    cst_types=(GoogleSection, NumPySection),
    enabled_by_default=False,
    activation_condition=ActivationCondition("class_docstring_style", frozenset({"class"})),
)
def cls203(node: GoogleSection | NumPySection, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """__init__ docstring has an Args/Parameters section but class_docstring_style is 'class'."""
    if ctx.config is None or ctx.config.class_docstring_style != "class":
        return
    if ctx.parent.name != "__init__":
        return
    if not is_param_section(node):
        return

    fix = delete_section_fix(ctx.docstring_text, node, Applicability.UNSAFE)
    yield make_diagnostic(
        "CLS203",
        ctx,
        "__init__ docstring should not have an Args/Parameters section when class_docstring_style is 'class'.",
        fix=fix,
        target=node,
    )
