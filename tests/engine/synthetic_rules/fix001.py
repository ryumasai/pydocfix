"""FIX001: synthetic rule that replaces 'x' with 'y' in summaries."""

from __future__ import annotations

from pydocstring import PlainDocstring

from pydocfix.edits import replace_token
from pydocfix.models import Applicability, Fix
from pydocfix.rules._base import BaseRule, DiagnoseContext


class FIX001(BaseRule[PlainDocstring]):
    """Synthetic fix rule that removes 'x' from summary text."""

    code = "FIX001"

    def diagnose(self, node: PlainDocstring, ctx: DiagnoseContext):
        if node.summary is None or "x" not in node.summary.text:
            return
        fixed = node.summary.text.replace("x", "y")
        fix = Fix(
            edits=[replace_token(node.summary, fixed)],
            applicability=Applicability.SAFE,
        )
        yield self._make_diagnostic(ctx, "Replace x with y", fix=fix, target=node.summary)
