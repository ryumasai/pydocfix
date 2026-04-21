"""Rule SUM002 - Summary should end with a period."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Final

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.diagnostics import Applicability, Diagnostic, Fix
from pydocfix.fixes import insert_at
from pydocfix.rules._base import BaseCtx, ClassCtx, FunctionCtx, ModuleCtx, make_diagnostic, rule

_DEFAULT_PERIOD: Final[str] = "."
_PERIOD_SET: Final[frozenset[str]] = frozenset([_DEFAULT_PERIOD, "!", "?"])


@rule(
    "SUM002",
    ctx_types=frozenset({FunctionCtx, ClassCtx, ModuleCtx}),
    cst_types=frozenset({GoogleDocstring, NumPyDocstring, PlainDocstring}),
)
def sum002(node: GoogleDocstring | NumPyDocstring | PlainDocstring, ctx: BaseCtx) -> Iterator[Diagnostic]:
    """Summary should end with a period."""
    root = node
    if root.summary is None:
        return

    token = root.summary
    summary: Final[str] = token.text.strip()
    last_char: Final[str | None] = summary[-1] if summary else None

    if last_char not in _PERIOD_SET:
        fix = Fix(
            edits=[insert_at(token.range.end, _DEFAULT_PERIOD)],
            applicability=Applicability.SAFE,
        )
        yield make_diagnostic("SUM002", ctx, "Summary should end with a period.", fix=fix, target=token)
