"""SAFE000: synthetic rule that also fixes VIOLATION(SAFE001) — used to test overlapping fix skipping."""

from __future__ import annotations

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.diagnostics import Applicability, Fix
from pydocfix.fixes import replace_token
from pydocfix.rules._base import BaseRule, DiagnoseContext

_VIOLATION = "VIOLATION(SAFE001)"
_FIXED = "FIXED(SAFE000)."


class SAFE000(BaseRule[GoogleDocstring | NumPyDocstring | PlainDocstring]):
    """Detects VIOLATION(SAFE001) and proposes a competing fix over the same token."""

    code = "SAFE000"

    def diagnose(self, node, ctx: DiagnoseContext):
        if node.summary is None or _VIOLATION not in node.summary.text:
            return
        fix = Fix(
            edits=[replace_token(node.summary, _FIXED)],
            applicability=Applicability.SAFE,
        )
        yield self._make_diagnostic(ctx, f"Summary contains {_VIOLATION!r}", fix=fix, target=node.summary)
