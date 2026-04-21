"""Rule PRM103 - Parameter has no type in docstring."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleArg, NumPyParameter

from pydocfix.diagnostics import Applicability, Diagnostic, Edit, Fix
from pydocfix.rules._base import ActivationCondition, FunctionCtx, make_diagnostic, rule
from pydocfix.rules.prm.helpers import bare_name, get_annotation_map, get_param_name_token


def _build_insert_type_fix(cst_node: GoogleArg | NumPyParameter, ann: str) -> Fix:
    """Build a fix that inserts the type annotation into the docstring entry."""
    if isinstance(cst_node, GoogleArg):
        name_token = cst_node.name
        if name_token is None:
            return Fix(edits=[], applicability=Applicability.UNSAFE)
        insert_pos = name_token.range.end
        return Fix(
            edits=[Edit(start=insert_pos, end=insert_pos, new_text=f" ({ann})")],
            applicability=Applicability.UNSAFE,
        )
    else:  # NumPyParameter
        name_token = cst_node.names[0] if cst_node.names else None
        if name_token is None:
            return Fix(edits=[], applicability=Applicability.UNSAFE)
        if cst_node.colon:
            insert_pos = cst_node.colon.range.end
            return Fix(
                edits=[Edit(start=insert_pos, end=insert_pos, new_text=f" {ann}")],
                applicability=Applicability.UNSAFE,
            )
        else:
            insert_pos = name_token.range.end
            return Fix(
                edits=[Edit(start=insert_pos, end=insert_pos, new_text=f" : {ann}")],
                applicability=Applicability.UNSAFE,
            )


@rule(
    "PRM103",
    ctx_types=frozenset({FunctionCtx}),
    cst_types=frozenset({GoogleArg, NumPyParameter}),
    enabled_by_default=False,
    conflicts_with=frozenset({"PRM104"}),
    activation_condition=ActivationCondition("type_annotation_style", frozenset({"docstring", "both"})),
)
def prm103(node: GoogleArg | NumPyParameter, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Docstring parameter has no type annotation (type_annotation_style = "docstring")."""
    cst_node = node

    if isinstance(cst_node, GoogleArg):
        name_token = get_param_name_token(cst_node)
        type_token = cst_node.type
    else:
        name_token = get_param_name_token(cst_node)
        type_token = cst_node.type
    if name_token is None:
        return
    if type_token is not None and type_token.text.strip():
        return

    b = bare_name(name_token.text)
    ann = get_annotation_map(ctx.parent).get(b)
    fix = None
    if ann:
        fix = _build_insert_type_fix(cst_node, ann)

    message = f"Parameter '{name_token.text}' has no type in docstring."
    yield make_diagnostic("PRM103", ctx, message, fix=fix, target=name_token)
