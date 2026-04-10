"""Rule SUM002 - Summary should end with a period."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Final

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.rules._base import Applicability, BaseRule, DiagnoseContext, Diagnostic, Fix, insert_at

_DEFAULT_PERIOD: Final[str] = "."
_PERIOD_SET: Final[frozenset[str]] = frozenset([_DEFAULT_PERIOD, "!", "?"])


class SUM002(BaseRule):
    """Summary should end with a period."""

    code = "SUM002"
    message = "Summary should end with a period."
    target_kinds = frozenset(
        {
            GoogleDocstring,
            NumPyDocstring,
            PlainDocstring,
        }
    )

    def diagnose(self, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        root = ctx.target_cst
        if not isinstance(root, (GoogleDocstring, NumPyDocstring, PlainDocstring)):
            return
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
            yield self._make_diagnostic(ctx, self.message, fix=fix, target=token)
