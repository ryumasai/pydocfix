"""Rule RTN103 - Return has no type in docstring."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleReturn, NumPyReturns

from pydocfix.diagnostics import Applicability, Diagnostic, Edit, Fix
from pydocfix.rules._base import ActivationCondition, FunctionCtx, make_diagnostic, rule


@rule(
    "RTN103",
    ctx_types=frozenset({FunctionCtx}),
    cst_types=frozenset({GoogleReturn, NumPyReturns}),
    enabled_by_default=False,
    conflicts_with=frozenset({"RTN104"}),
    activation_condition=ActivationCondition("type_annotation_style", frozenset({"docstring", "both"})),
)
def rtn103(node: GoogleReturn | NumPyReturns, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Docstring return entry has no type (type_annotation_style = "docstring")."""
    cst_node = node

    ret_type_token = cst_node.return_type
    if ret_type_token is not None and ret_type_token.text.strip():
        return  # Already has type

    # Try to get type from signature for the fix
    func = ctx.parent
    ann = None
    if func.returns is not None:
        ann = ast.unparse(func.returns)

    fix = None
    if ann:
        if isinstance(cst_node, GoogleReturn):
            fix = Fix(
                edits=[Edit(start=cst_node.range.start, end=cst_node.range.start, new_text=f"{ann}: ")],
                applicability=Applicability.UNSAFE,
            )
        else:  # NumPyReturns
            fix = Fix(
                edits=[Edit(start=cst_node.range.start, end=cst_node.range.start, new_text=f"{ann}\n")],
                applicability=Applicability.UNSAFE,
            )

    yield make_diagnostic("RTN103", ctx, "Return has no type in docstring.", fix=fix, target=cst_node)
