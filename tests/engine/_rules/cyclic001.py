"""CYCLIC001: synthetic rule that never converges — each fix re-introduces the violation."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.diagnostics import Applicability, Diagnostic, Fix
from pydocfix.fixes import replace_token
from pydocfix.rules._base import BaseCtx, ClassCtx, FunctionCtx, ModuleCtx, make_diagnostic, rule

_TRIGGER = "CYCLIC"


@rule(
    "CYCLIC001", ctx_types=frozenset({FunctionCtx, ClassCtx, ModuleCtx}), cst_types=frozenset({GoogleDocstring, NumPyDocstring, PlainDocstring})
)
def cyclic001(node: GoogleDocstring | NumPyDocstring | PlainDocstring, ctx: BaseCtx) -> Iterator[Diagnostic]:
    """Fires on any summary containing 'CYCLIC' and fixes it to another 'CYCLIC' string."""
    if node.summary is None or _TRIGGER not in node.summary.text:
        return
    # Fix replaces the current text with another string that also contains CYCLIC,
    # so the rule fires again on the next iteration — never converges.
    new_text = node.summary.text.replace(_TRIGGER, f"({_TRIGGER})")
    fix = Fix(
        edits=[replace_token(node.summary, new_text)],
        applicability=Applicability.SAFE,
    )
    yield make_diagnostic("CYCLIC001", ctx, f"Summary contains {_TRIGGER!r}", fix=fix, target=node.summary)
