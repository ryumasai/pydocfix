"""SUP001: synthetic rule that flags summaries containing 'x'."""

from __future__ import annotations

from pydocstring import PlainDocstring

from pydocfix.rules._base import BaseRule, DiagnoseContext


class SUP001(BaseRule[PlainDocstring]):
    """Synthetic rule used to test noqa usage tracking."""

    code = "SUP001"

    def diagnose(self, node: PlainDocstring, ctx: DiagnoseContext):
        if node.summary is not None and "x" in node.summary.text:
            yield self._make_diagnostic(ctx, "Contains x", target=node.summary)
