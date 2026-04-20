"""Rule PRM101 - Docstring parameter type does not match type hint."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleArg, NumPyParameter

from pydocfix.diagnostics import Applicability, Diagnostic, Fix
from pydocfix.fixes import replace_token
from pydocfix.rules._base import FunctionCtx, make_diagnostic, rule
from pydocfix.rules.helpers import normalize_optional
from pydocfix.rules.prm.helpers import get_annotation_map, get_param_name_token


@rule("PRM101", targets=FunctionCtx, cst_types=(GoogleArg, NumPyParameter))
def prm101(node: GoogleArg | NumPyParameter, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Docstring parameter type does not match type hint."""
    cst_node = node

    name_token = get_param_name_token(cst_node)
    type_token = cst_node.type
    if name_token is None or type_token is None:
        return

    ann_map = get_annotation_map(ctx.parent)
    param_name = name_token.text
    hint_type = ann_map.get(param_name)
    if hint_type is None:
        return

    doc_type = type_token.text
    cmp_hint = hint_type
    cmp_doc = doc_type
    if ctx.config is not None and ctx.config.allow_optional_shorthand:
        cmp_hint = normalize_optional(hint_type)
        cmp_doc = normalize_optional(doc_type)
    if cmp_doc == cmp_hint:
        return

    fix = Fix(
        edits=[replace_token(type_token, hint_type)],
        applicability=Applicability.UNSAFE,
    )
    message = f"Docstring type '{doc_type}' does not match type hint '{hint_type}' for parameter '{param_name}'."
    yield make_diagnostic("PRM101", ctx, message, fix=fix, target=type_token)
