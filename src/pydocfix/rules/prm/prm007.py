"""Rule PRM007 - Duplicate parameter in docstring."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import (
    GoogleSection,
    NumPySection,
)

from pydocfix.diagnostics import Applicability, Diagnostic
from pydocfix.rules._base import FunctionCtx, make_diagnostic, rule
from pydocfix.rules.helpers import delete_entry_fix
from pydocfix.rules.prm.helpers import (
    get_documented_param_nodes,
    get_param_name_token,
    is_param_section,
)


@rule("PRM007", ctx_types=frozenset({FunctionCtx}), cst_types=frozenset({GoogleSection, NumPySection}))
def prm007(node: GoogleSection | NumPySection, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Docstring documents a parameter more than once."""
    section = node
    if not is_param_section(section):
        return

    entries = [
        (name, node, get_param_name_token(node))
        for name, node in get_documented_param_nodes(ctx.docstring_cst, section)
    ]

    seen: set[str] = set()
    for name, param_node, name_token in entries:
        if name_token is None:
            continue
        if name in seen:
            fix = delete_entry_fix(ctx.docstring_text, param_node.range, Applicability.UNSAFE)
            message = f"Parameter '{name}' is documented more than once."
            yield make_diagnostic("PRM007", ctx, message, fix=fix, target=name_token)
        else:
            seen.add(name)
