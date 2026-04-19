"""ALWAYS001: synthetic rule that fires on every docstring (no fix)."""

from __future__ import annotations

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.rules._base import BaseRule, DiagnoseContext


class ALWAYS001(BaseRule[GoogleDocstring | NumPyDocstring | PlainDocstring]):
    """Fires a diagnostic on every docstring regardless of content."""

    code = "ALWAYS001"

    def diagnose(self, node, ctx: DiagnoseContext):
        yield self._make_diagnostic(ctx, "Always fires on every docstring", target=node)
