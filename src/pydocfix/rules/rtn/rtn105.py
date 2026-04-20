"""Rule RTN105 - Return type has no annotation in function signature."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleReturn, NumPyReturns

from pydocfix.diagnostics import Diagnostic
from pydocfix.rules._base import ActivationCondition, FunctionCtx, make_diagnostic, rule


@rule(
    "RTN105",
    targets=FunctionCtx,
    cst_types=(GoogleReturn, NumPyReturns),
    enabled_by_default=False,
    conflicts_with=frozenset({"RTN102", "RTN106"}),
    activation_condition=ActivationCondition("type_annotation_style", frozenset({"signature", "both"})),
)
def rtn105(node: GoogleReturn | NumPyReturns, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Documented return has no type annotation in the function signature."""
    cst_node = node

    func = ctx.parent
    if func.returns is not None:
        return  # has annotation in signature

    yield make_diagnostic("RTN105", ctx, "Return has no type annotation in signature.", target=cst_node)
