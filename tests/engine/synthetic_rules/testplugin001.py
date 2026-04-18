"""TESTPLUGIN001: synthetic rule that flags short docstring summaries."""

from __future__ import annotations

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.rules._base import BaseRule, DiagnoseContext


class TESTPLUGIN001(BaseRule[GoogleDocstring | NumPyDocstring | PlainDocstring]):
    """Test plugin rule that flags any short single-line docstring summary."""

    code = "TESTPLUGIN001"
    enabled_by_default = True

    def diagnose(self, node, ctx: DiagnoseContext):
        summary = node.summary
        if summary is not None and len(summary.text.strip()) < 5:
            yield self._make_diagnostic(ctx, "Docstring summary too short", target=node)
