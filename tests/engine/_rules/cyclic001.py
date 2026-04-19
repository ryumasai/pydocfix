"""CYCLIC001: synthetic rule that never converges — each fix re-introduces the violation."""

from __future__ import annotations

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.edits import replace_token
from pydocfix.diagnostics import Applicability, Fix
from pydocfix.rules._base import BaseRule, DiagnoseContext

_TRIGGER = "CYCLIC"


class CYCLIC001(BaseRule[GoogleDocstring | NumPyDocstring | PlainDocstring]):
    """Fires on any summary containing 'CYCLIC' and fixes it to another 'CYCLIC' string."""

    code = "CYCLIC001"

    def diagnose(self, node, ctx: DiagnoseContext):
        if node.summary is None or _TRIGGER not in node.summary.text:
            return
        # Fix replaces the current text with another string that also contains CYCLIC,
        # so the rule fires again on the next iteration — never converges.
        new_text = node.summary.text.replace(_TRIGGER, f"({_TRIGGER})")
        fix = Fix(
            edits=[replace_token(node.summary, new_text)],
            applicability=Applicability.SAFE,
        )
        yield self._make_diagnostic(ctx, f"Summary contains {_TRIGGER!r}", fix=fix, target=node.summary)
