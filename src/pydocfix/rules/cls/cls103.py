"""Rule CLS103 - Class docstring has an Args section (style='init')."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleSection, NumPySection

from pydocfix.diagnostics import Applicability, Diagnostic
from pydocfix.rules._base import ActivationCondition, ClassCtx, make_diagnostic, rule
from pydocfix.rules.cls.helpers import is_param_section
from pydocfix.rules.helpers import delete_section_fix


@rule(
    "CLS103",
    targets=ClassCtx,
    cst_types=(GoogleSection, NumPySection),
    enabled_by_default=False,
    activation_condition=ActivationCondition("class_docstring_style", frozenset({"init"})),
)
def cls103(node: GoogleSection | NumPySection, ctx: ClassCtx) -> Iterator[Diagnostic]:
    """Class docstring has an Args/Parameters section but class_docstring_style is 'init'."""
    if ctx.config is None or ctx.config.class_docstring_style != "init":
        return
    if not is_param_section(node):
        return

    fix = delete_section_fix(ctx.docstring_text, node, Applicability.UNSAFE)
    yield make_diagnostic(
        "CLS103",
        ctx,
        "Class docstring should not have an Args/Parameters section when class_docstring_style is 'init'.",
        fix=fix,
        target=node,
    )
