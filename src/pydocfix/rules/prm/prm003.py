"""Rule PRM003 - Docstring documents ``self`` or ``cls``."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleArg, NumPyParameter

from pydocfix.rules._base import Applicability, BaseRule, DiagnoseContext, Diagnostic, Fix, delete_range


class PRM003(BaseRule):
    """Docstring should not document ``self`` or ``cls``."""

    code = "PDX-PRM003"
    message = "Docstring should not document \'self\' or \'cls\'."
    target_kinds = {
        GoogleArg,
        NumPyParameter,
    }

    def diagnose(self, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = ctx.target_cst
        if not isinstance(cst_node, (GoogleArg, NumPyParameter)):
            return
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        name_token = cst_node.name if isinstance(cst_node, GoogleArg) else None
        if isinstance(cst_node, NumPyParameter):
            name_token = cst_node.names[0] if cst_node.names else None
        if name_token is None:
            return

        if name_token.text not in ("self", "cls"):
            return

        # Delete the entire param entry line(s)
        ds_bytes = ctx.docstring_text.encode("utf-8")
        nl_before = ds_bytes.rfind(b"\n", 0, cst_node.range.start)
        start = nl_before + 1 if nl_before != -1 else cst_node.range.start
        nl_after = ds_bytes.find(b"\n", cst_node.range.end)
        end = nl_after + 1 if nl_after != -1 else cst_node.range.end

        fix = Fix(
            edits=[delete_range(start, end)],
            applicability=Applicability.SAFE,
        )
        message = f"Docstring should not document \'{name_token.text}\'."
        yield self._make_diagnostic(ctx, message, fix=fix, target=name_token)
