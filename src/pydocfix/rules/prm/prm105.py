"""Rule PRM105 - Parameter has no type annotation in function signature."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleArg, NumPyParameter

from pydocfix.diagnostics import Diagnostic
from pydocfix.rules._base import ActivationCondition, FunctionCtx, make_diagnostic, rule
from pydocfix.rules.prm.helpers import bare_name, get_annotation_map, get_param_name_token, get_signature_params


@rule(
    "PRM105",
    ctx_types=frozenset({FunctionCtx}),
    cst_types=frozenset({GoogleArg, NumPyParameter}),
    enabled_by_default=False,
    conflicts_with=frozenset({"PRM102", "PRM106"}),
    activation_condition=ActivationCondition("type_annotation_style", frozenset({"signature", "both"})),
)
def prm105(node: GoogleArg | NumPyParameter, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Documented parameter has no type annotation in the function signature."""
    cst_node = node

    name_token = get_param_name_token(cst_node)
    if name_token is None:
        return

    b = bare_name(name_token.text)
    sig_params = {bare_name(n) for n, _ in get_signature_params(ctx.parent)}
    if b not in sig_params:
        return  # not a real parameter — PRM005's responsibility

    ann_map = get_annotation_map(ctx.parent)
    if b in ann_map:
        return  # has annotation in signature

    message = f"Parameter '{name_token.text}' has no type annotation in signature."
    yield make_diagnostic("PRM105", ctx, message, target=name_token)
