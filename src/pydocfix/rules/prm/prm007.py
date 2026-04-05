"""Rule PRM007 - Duplicate parameter in docstring."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import (
    GoogleSection,
    NumPySection,
)

from pydocfix.rules._base import (
    Applicability,
    BaseRule,
    DiagnoseContext,
    Diagnostic,
)
from pydocfix.rules.prm._helpers import (
    delete_entry_fix,
    get_documented_param_nodes,
    get_param_name_token,
    is_param_section,
)


class PRM007(BaseRule):
    """Docstring documents a parameter more than once."""

    code = "PRM007"
    message = "Duplicate parameter in docstring."
    target_kinds = frozenset({
        GoogleSection,
        NumPySection,
    })

    def diagnose(self, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        section = ctx.target_cst
        if not isinstance(section, (GoogleSection, NumPySection)):
            return
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return
        if not is_param_section(section):
            return

        entries = [
            (name, node, get_param_name_token(node))
            for name, node in get_documented_param_nodes(ctx.docstring_cst, section)
        ]

        seen: set[str] = set()
        for name, param_node, name_token in entries:
            if name_token is None:
                continue
            if name in seen:
                fix = delete_entry_fix(ctx.docstring_text, param_node, Applicability.UNSAFE)
                message = f"Parameter '{name}' is documented more than once."
                yield self._make_diagnostic(ctx, message, fix=fix, target=name_token)
            else:
                seen.add(name)
