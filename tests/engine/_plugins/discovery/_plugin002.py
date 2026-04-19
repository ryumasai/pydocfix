"""PLUGIN002: underscore-prefixed file — must be skipped by discover_rules_in_path."""

from __future__ import annotations

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.rules._base import BaseRule, DiagnoseContext


class PLUGIN002(BaseRule[GoogleDocstring | NumPyDocstring | PlainDocstring]):
    """Plugin rule in a _-prefixed file; should never be discovered via path."""

    code = "PLUGIN002"

    def diagnose(self, node, ctx: DiagnoseContext):
        return iter(())
