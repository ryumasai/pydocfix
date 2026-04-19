"""DISPLAY001: synthetic rule with DISPLAY_ONLY fix — never applied by the fixer."""

from __future__ import annotations

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.edits import replace_token
from pydocfix.diagnostics import Applicability, Fix
from pydocfix.rules._base import BaseRule, DiagnoseContext

_VIOLATION = "VIOLATION(DISPLAY001)"


class DISPLAY001(BaseRule[GoogleDocstring | NumPyDocstring | PlainDocstring]):
    """Detects VIOLATION(DISPLAY001) and proposes a DISPLAY_ONLY fix (never applied)."""

    code = "DISPLAY001"

    def diagnose(self, node, ctx: DiagnoseContext):
        if node.summary is None or _VIOLATION not in node.summary.text:
            return
        fix = Fix(
            edits=[replace_token(node.summary, "FIXED(DISPLAY001).")],
            applicability=Applicability.DISPLAY_ONLY,
        )
        yield self._make_diagnostic(ctx, f"Summary contains {_VIOLATION!r}", fix=fix, target=node.summary)
