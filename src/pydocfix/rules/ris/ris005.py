"""Rule RIS005 - Docstring documents an exception not raised in function body."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleException, NumPyException

from pydocfix.diagnostics import Applicability, Diagnostic
from pydocfix.rules._base import FunctionCtx, make_diagnostic, rule
from pydocfix.rules.helpers import delete_entry_fix
from pydocfix.rules.ris.helpers import _bare_exc_name, get_raised_exceptions


@rule("RIS005", ctx_types=frozenset({FunctionCtx}), cst_types=frozenset({GoogleException, NumPyException}))
def ris005(node: GoogleException | NumPyException, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Raises entry documents an exception not raised in the function body."""
    cst_node = node

    type_token = cst_node.type
    if type_token is None:
        return

    documented_name = _bare_exc_name(type_token.text)
    raised_names = {_bare_exc_name(e) for e in get_raised_exceptions(ctx.parent)}

    if documented_name in raised_names:
        return

    fix = delete_entry_fix(ctx.docstring_text, cst_node.range, Applicability.UNSAFE)

    message = f"Raises entry '{type_token.text}' not raised in function body."
    yield make_diagnostic("RIS005", ctx, message, fix=fix, target=type_token)
