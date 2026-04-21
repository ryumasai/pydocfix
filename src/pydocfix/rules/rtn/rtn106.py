"""Rule RTN106 - Return type has an annotation in function signature (docstring style)."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleReturn, NumPyReturns

from pydocfix.diagnostics import Diagnostic
from pydocfix.rules._base import ActivationCondition, FunctionCtx, make_diagnostic, rule


@rule(
    "RTN106",
    ctx_types=frozenset({FunctionCtx}),
    cst_types=frozenset({GoogleReturn, NumPyReturns}),
    enabled_by_default=False,
    conflicts_with=frozenset({"RTN105"}),
    activation_condition=ActivationCondition("type_annotation_style", frozenset({"docstring"})),
)
def rtn106(node: GoogleReturn | NumPyReturns, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Documented return has a type annotation in the function signature (types belong in docstring)."""
    cst_node = node

    func = ctx.parent
    if func.returns is None:
        return  # no annotation in signature — nothing to flag

    yield make_diagnostic(
        "RTN106", ctx, "Return has a type annotation in signature; types belong in the docstring.", target=cst_node
    )
