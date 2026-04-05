"""Rule SUM001 - Docstring has no summary line."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.rules._base import BaseRule, DiagnoseContext, Diagnostic


class SUM001(BaseRule):
    """Docstring has no summary line."""

    code = "SUM001"
    message = "Docstring has no summary line."
    target_kinds = frozenset({
        GoogleDocstring,
        NumPyDocstring,
        PlainDocstring,
    })

    @staticmethod
    def _has_summary(root: GoogleDocstring | NumPyDocstring | PlainDocstring) -> bool:
        """Return True if the docstring contains a non-empty summary token."""
        if root.summary is None:
            return False
        text = root.summary.text
        return bool(text and text.strip())

    def diagnose(self, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        root = ctx.target_cst
        if not isinstance(root, (GoogleDocstring, NumPyDocstring, PlainDocstring)):
            return
        if self._has_summary(root):
            return
        yield self._make_diagnostic(ctx, self.message, target=root)
