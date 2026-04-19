"""Rule SUM001 - Docstring has no summary line."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.diagnostics import Diagnostic
from pydocfix.rules._base import BaseRule, DiagnoseContext


class SUM001(BaseRule[GoogleDocstring | NumPyDocstring | PlainDocstring]):
    """Docstring has no summary line."""

    code = "SUM001"

    @staticmethod
    def _has_summary(root: GoogleDocstring | NumPyDocstring | PlainDocstring) -> bool:
        """Return True if the docstring contains a non-empty summary token."""
        if root.summary is None:
            return False
        text = root.summary.text
        return bool(text and text.strip())

    def diagnose(
        self, node: GoogleDocstring | NumPyDocstring | PlainDocstring, ctx: DiagnoseContext
    ) -> Iterator[Diagnostic]:
        root = node
        if self._has_summary(root):
            return
        yield self._make_diagnostic(ctx, "Docstring has no summary line.", target=root)
