"""Rule YLD105 - Yield type has no annotation in function signature."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleYield, NumPyYields

from pydocfix.diagnostics import Diagnostic
from pydocfix.rules._base import ActivationCondition, FunctionCtx, make_diagnostic, rule
from pydocfix.rules.yld.helpers import get_yield_type


@rule(
    "YLD105",
    targets=FunctionCtx,
    cst_types=(GoogleYield, NumPyYields),
    enabled_by_default=False,
    conflicts_with=frozenset({"YLD102", "YLD106"}),
    activation_condition=ActivationCondition("type_annotation_style", frozenset({"signature", "both"})),
)
def yld105(node: GoogleYield | NumPyYields, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Documented yield has no type annotation in the function signature."""
    cst_node = node

    if get_yield_type(ctx.parent) is not None:
        return  # has annotation in signature

    yield make_diagnostic("YLD105", ctx, "Yield has no type annotation in signature.", target=cst_node)
