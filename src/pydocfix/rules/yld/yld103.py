"""Rule YLD103 - Yield has no type in docstring."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleYield, NumPyYields

from pydocfix.diagnostics import Applicability, Diagnostic, Edit, Fix
from pydocfix.rules._base import ActivationCondition, FunctionCtx, make_diagnostic, rule
from pydocfix.rules.yld.helpers import get_yield_type


@rule(
    "YLD103",
    targets=FunctionCtx,
    cst_types=(GoogleYield, NumPyYields),
    enabled_by_default=False,
    conflicts_with=frozenset({"YLD104"}),
    activation_condition=ActivationCondition("type_annotation_style", frozenset({"docstring", "both"})),
)
def yld103(node: GoogleYield | NumPyYields, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Docstring yield entry has no type (type_annotation_style = "docstring")."""
    cst_node = node

    ret_type_token = cst_node.return_type
    if ret_type_token is not None and ret_type_token.text.strip():
        return

    ann = get_yield_type(ctx.parent)
    fix = None
    if ann:
        if isinstance(cst_node, GoogleYield):
            fix = Fix(
                edits=[Edit(start=cst_node.range.start, end=cst_node.range.start, new_text=f"{ann}: ")],
                applicability=Applicability.UNSAFE,
            )
        else:  # NumPyYields
            fix = Fix(
                edits=[Edit(start=cst_node.range.start, end=cst_node.range.start, new_text=f"{ann}\n")],
                applicability=Applicability.UNSAFE,
            )

    yield make_diagnostic("YLD103", ctx, "Yield has no type in docstring.", fix=fix, target=cst_node)
