"""Rule RIS005 - Docstring documents an exception not raised in function body."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleException, NumPyException

from pydocfix.rules._base import Applicability, BaseRule, DiagnoseContext, Diagnostic
from pydocfix.rules._helpers import delete_entry_fix
from pydocfix.rules.ris._helpers import _bare_exc_name, get_raised_exceptions


class RIS005(BaseRule[GoogleException | NumPyException]):
    """Raises entry documents an exception not raised in the function body."""

    code = "RIS005"

    def diagnose(self, node: GoogleException | NumPyException, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = node
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        type_token = cst_node.type
        if type_token is None:
            return

        documented_name = _bare_exc_name(type_token.text)
        raised_names = {_bare_exc_name(e) for e in get_raised_exceptions(ctx.parent_ast)}

        if documented_name in raised_names:
            return

        fix = delete_entry_fix(ctx.docstring_text, cst_node.range, Applicability.UNSAFE)

        message = f"Raises entry '{type_token.text}' not raised in function body."
        yield self._make_diagnostic(ctx, message, fix=fix, target=type_token)
