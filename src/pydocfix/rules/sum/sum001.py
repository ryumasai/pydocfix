"""Rule SUM001 - Docstring has no summary line."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.diagnostics import Diagnostic
from pydocfix.rules._base import BaseCtx, ClassCtx, FunctionCtx, ModuleCtx, make_diagnostic, rule


def _has_summary(root: GoogleDocstring | NumPyDocstring | PlainDocstring) -> bool:
    """Return True if the docstring contains a non-empty summary token."""
    if root.summary is None:
        return False
    text = root.summary.text
    return bool(text and text.strip())


@rule("SUM001", ctx_types=frozenset({FunctionCtx, ClassCtx, ModuleCtx}), cst_types=frozenset({GoogleDocstring, NumPyDocstring, PlainDocstring}))
def sum001(node: GoogleDocstring | NumPyDocstring | PlainDocstring, ctx: BaseCtx) -> Iterator[Diagnostic]:
    """Docstring has no summary line."""
    root = node
    if _has_summary(root):
        return
    yield make_diagnostic("SUM001", ctx, "Docstring has no summary line.", target=root)
