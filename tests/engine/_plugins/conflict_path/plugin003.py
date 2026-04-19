"""PLUGIN003 (paths side): loses to the conflict_mod version in precedence test."""

from __future__ import annotations

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.rules._base import BaseRule, DiagnoseContext


class PLUGIN003(BaseRule[GoogleDocstring | NumPyDocstring | PlainDocstring]):
    """PLUGIN003 loaded via plugin_paths (lower precedence)."""

    code = "PLUGIN003"

    def diagnose(self, node, ctx: DiagnoseContext):
        return iter(())
