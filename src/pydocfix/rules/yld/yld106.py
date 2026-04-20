"""Rule YLD106 - Yield type has an annotation in function signature (docstring style)."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleYield, NumPyYields

from pydocfix.diagnostics import Diagnostic
from pydocfix.rules._base import ActivationCondition, FunctionCtx, make_diagnostic, rule
from pydocfix.rules.yld.helpers import get_yield_type


@rule(
    "YLD106",
    targets=FunctionCtx,
    cst_types=(GoogleYield, NumPyYields),
    enabled_by_default=False,
    conflicts_with=frozenset({"YLD105"}),
    activation_condition=ActivationCondition("type_annotation_style", frozenset({"docstring"})),
)
def yld106(node: GoogleYield | NumPyYields, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Documented yield has a type annotation in the function signature (types belong in docstring)."""
    cst_node = node

    if get_yield_type(ctx.parent) is None:
        return  # no annotation in signature — nothing to flag

    yield make_diagnostic(
        "YLD106", ctx, "Yield has a type annotation in signature; types belong in the docstring.", target=cst_node
    )
