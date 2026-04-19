"""PLUGIN003 (modules side): wins in the plugin_modules vs plugin_paths precedence test."""

from __future__ import annotations

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.rules._base import BaseRule, DiagnoseContext


class PLUGIN003(BaseRule[GoogleDocstring | NumPyDocstring | PlainDocstring]):
    """PLUGIN003 loaded via plugin_modules (higher precedence)."""

    code = "PLUGIN003"

    def diagnose(self, node, ctx: DiagnoseContext):
        return iter(())
