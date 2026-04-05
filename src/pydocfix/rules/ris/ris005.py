"""Rule RIS005 - Docstring documents an exception not raised in function body."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleException, NumPyException

from pydocfix.rules._base import Applicability, BaseRule, DiagnoseContext, Diagnostic, Fix, delete_range
from pydocfix.rules.ris._helpers import _bare_exc_name, get_raised_exceptions


class RIS005(BaseRule):
    """Raises entry documents an exception not raised in the function body."""

    code = "RIS005"
    message = "Raises entry documents exception not raised in function body."
    target_kinds = frozenset({
        GoogleException,
        NumPyException,
    })

    def diagnose(self, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = ctx.target_cst
        if not isinstance(cst_node, (GoogleException, NumPyException)):
            return
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        type_token = cst_node.type
        if type_token is None:
            return

        documented_name = _bare_exc_name(type_token.text)
        raised_names = {_bare_exc_name(e) for e in get_raised_exceptions(ctx.parent_ast)}

        if documented_name in raised_names:
            return

        ds_bytes = ctx.docstring_text.encode("utf-8")
        nl_before = ds_bytes.rfind(b"\n", 0, cst_node.range.start)
        start = nl_before + 1 if nl_before != -1 else cst_node.range.start
        nl_after = ds_bytes.find(b"\n", cst_node.range.end)
        end = nl_after + 1 if nl_after != -1 else cst_node.range.end

        fix = Fix(
            edits=[delete_range(start, end)],
            applicability=Applicability.UNSAFE,
        )
        message = f"Raises entry '{type_token.text}' not raised in function body."
        yield self._make_diagnostic(ctx, message, fix=fix, target=type_token)
