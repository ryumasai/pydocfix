"""Rule PRM106 - Parameter has a type annotation in function signature (docstring style)."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleArg, NumPyParameter

from pydocfix.rules._base import ActivationCondition, BaseRule, DiagnoseContext, Diagnostic
from pydocfix.rules.prm._helpers import bare_name, get_annotation_map, get_param_name_token, get_signature_params


class PRM106(BaseRule[GoogleArg | NumPyParameter]):
    """Documented parameter has a type annotation in the function signature (types belong in docstring)."""

    code = "PRM106"
    enabled_by_default = False
    conflicts_with = frozenset({"PRM105"})
    activation_condition = ActivationCondition("type_annotation_style", frozenset({"docstring"}))

    def diagnose(self, node: GoogleArg | NumPyParameter, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = node
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        name_token = get_param_name_token(cst_node)
        if name_token is None:
            return

        b = bare_name(name_token.text)
        sig_params = {bare_name(n) for n, _ in get_signature_params(ctx.parent_ast)}
        if b not in sig_params:
            return  # not a real parameter — PRM005's responsibility

        ann_map = get_annotation_map(ctx.parent_ast)
        if b not in ann_map:
            return  # no annotation in signature — nothing to flag

        message = f"Parameter '{name_token.text}' has a type annotation in signature; types belong in the docstring."
        yield self._make_diagnostic(ctx, message, target=name_token)
