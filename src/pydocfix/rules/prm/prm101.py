"""Rule PRM101 - Docstring parameter type does not match type hint."""

from __future__ import annotations

import ast
from collections.abc import Iterator
from typing import TYPE_CHECKING

from pydocstring import GoogleArg, NumPyParameter

from pydocfix.rules._base import Applicability, BaseRule, DiagnoseContext, Diagnostic, Fix, replace_token
from pydocfix.rules.prm._helpers import get_annotation_map, get_param_name_token

if TYPE_CHECKING:
    from pydocfix.config import Config


class PRM101(BaseRule):
    """Docstring parameter type does not match type hint."""

    code = "PRM101"
    message = "Docstring parameter type does not match type hint."
    target_kinds = {
        GoogleArg,
        NumPyParameter,
    }

    def __init__(self, config: Config | None = None):
        super().__init__(config)
        self._ann_cache: tuple[int, dict[str, str]] = (0, {})

    def _get_annotation_map(self, ast_node: ast.AST) -> dict[str, str]:
        """Return annotation map for ast_node, with per-call caching."""
        node_id = id(ast_node)
        if self._ann_cache[0] == node_id:
            return self._ann_cache[1]
        if not isinstance(ast_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return {}
        result = get_annotation_map(ast_node)
        self._ann_cache = (node_id, result)
        return result

    def diagnose(self, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = ctx.target_cst
        if not isinstance(cst_node, (GoogleArg, NumPyParameter)):
            return

        if isinstance(cst_node, GoogleArg):
            name_token = get_param_name_token(cst_node)
            type_token = cst_node.type
        else:
            name_token = get_param_name_token(cst_node)
            type_token = cst_node.type
        if name_token is None or type_token is None:
            return

        ann_map = self._get_annotation_map(ctx.parent_ast)
        param_name = name_token.text
        hint_type = ann_map.get(param_name)
        if hint_type is None:
            return

        doc_type = type_token.text
        if doc_type == hint_type:
            return

        fix = Fix(
            edits=[replace_token(type_token, hint_type)],
            applicability=Applicability.UNSAFE,
        )
        message = f"Docstring type '{doc_type}' does not match type hint '{hint_type}' for parameter '{param_name}'."
        yield self._make_diagnostic(ctx, message, fix=fix, target=type_token)
