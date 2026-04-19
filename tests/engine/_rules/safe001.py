"""SAFE001: synthetic rule that detects and safely fixes VIOLATION(SAFE001) in summary."""

from __future__ import annotations

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.edits import replace_token
from pydocfix.models import Applicability, Fix
from pydocfix.rules._base import BaseRule, DiagnoseContext

_VIOLATION = "VIOLATION(SAFE001)"
_FIXED = "FIXED(SAFE001)."


class SAFE001(BaseRule[GoogleDocstring | NumPyDocstring | PlainDocstring]):
    """Detects VIOLATION(SAFE001) in docstring summary and fixes it safely."""

    code = "SAFE001"

    def diagnose(self, node, ctx: DiagnoseContext):
        if node.summary is None or _VIOLATION not in node.summary.text:
            return
        fix = Fix(
            edits=[replace_token(node.summary, _FIXED)],
            applicability=Applicability.SAFE,
        )
        yield self._make_diagnostic(ctx, f"Summary contains {_VIOLATION!r}", fix=fix, target=node.summary)
