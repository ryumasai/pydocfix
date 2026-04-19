"""PLUGIN001: minimal plugin rule for path-based discovery tests."""

from __future__ import annotations

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.rules._base import BaseRule, DiagnoseContext


class PLUGIN001(BaseRule[GoogleDocstring | NumPyDocstring | PlainDocstring]):
    """Minimal plugin rule; always a no-op."""

    code = "PLUGIN001"

    def diagnose(self, node, ctx: DiagnoseContext):
        return iter(())
