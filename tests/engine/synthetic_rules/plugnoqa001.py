"""PLUGNOQA001: synthetic rule for noqa suppression testing."""

from __future__ import annotations

from pydocfix.rules._base import BaseRule, DiagnoseContext


class PLUGNOQA001(BaseRule):
    """Test plugin rule for noqa suppression testing."""

    code = "PLUGNOQA001"
    enabled_by_default = True

    def diagnose(self, node, ctx: DiagnoseContext):
        yield self._make_diagnostic(ctx, "Plugin violation", target=node)
