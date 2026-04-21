"""Rule RTN104 - Redundant return type in docstring when signature has annotation."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleReturn, NumPyReturns

from pydocfix.diagnostics import Applicability, Diagnostic, Fix
from pydocfix.fixes import delete_range
from pydocfix.rules._base import ActivationCondition, FunctionCtx, make_diagnostic, rule


@rule(
    "RTN104",
    ctx_types=frozenset({FunctionCtx}),
    cst_types=frozenset({GoogleReturn, NumPyReturns}),
    enabled_by_default=False,
    conflicts_with=frozenset({"RTN103"}),
    activation_condition=ActivationCondition("type_annotation_style", frozenset({"signature"})),
)
def rtn104(node: GoogleReturn | NumPyReturns, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Signature has return type annotation but docstring also specifies type (redundant)."""
    cst_node = node

    ret_type_token = cst_node.return_type
    if ret_type_token is None:
        return  # No type in docstring — nothing to flag

    func = ctx.parent
    if func.returns is None:
        return  # No return annotation in signature — not redundant

    colon_token = cst_node.colon
    ds_bytes = ctx.docstring_text.encode("utf-8")

    if isinstance(cst_node, GoogleReturn) and colon_token:
        end = colon_token.range.end
        if end < len(ds_bytes) and ds_bytes[end : end + 1] == b" ":
            end += 1
        fix = Fix(
            edits=[delete_range(ret_type_token.range.start, end)],
            applicability=Applicability.SAFE,
        )
    elif isinstance(cst_node, NumPyReturns):
        nl_after = ds_bytes.find(b"\n", ret_type_token.range.end)
        end = nl_after + 1 if nl_after != -1 else ret_type_token.range.end
        fix = Fix(
            edits=[delete_range(ret_type_token.range.start, end)],
            applicability=Applicability.SAFE,
        )
    else:
        fix = Fix(edits=[], applicability=Applicability.SAFE)

    yield make_diagnostic(
        "RTN104",
        ctx,
        "Redundant return type in docstring; type annotation exists in signature.",
        fix=fix,
        target=ret_type_token,
    )
