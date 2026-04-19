"""UNSAFE001: synthetic rule that detects and unsafely fixes VIOLATION(UNSAFE001) in summary."""

from __future__ import annotations

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.edits import replace_token
from pydocfix.diagnostics import Applicability, Fix
from pydocfix.rules._base import BaseRule, DiagnoseContext

_VIOLATION = "VIOLATION(UNSAFE001)"
_FIXED = "FIXED(UNSAFE001)."


class UNSAFE001(BaseRule[GoogleDocstring | NumPyDocstring | PlainDocstring]):
    """Detects VIOLATION(UNSAFE001) in docstring summary and fixes it unsafely."""

    code = "UNSAFE001"

    def diagnose(self, node, ctx: DiagnoseContext):
        if node.summary is None or _VIOLATION not in node.summary.text:
            return
        fix = Fix(
            edits=[replace_token(node.summary, _FIXED)],
            applicability=Applicability.UNSAFE,
        )
        yield self._make_diagnostic(ctx, f"Summary contains {_VIOLATION!r}", fix=fix, target=node.summary)
