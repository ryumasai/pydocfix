"""Rule PRM004 - Missing parameter in docstring."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import (
    GoogleSection,
    NumPySection,
)

from pydocfix.diagnostics import Applicability, Diagnostic, Fix
from pydocfix.fixes import insert_at
from pydocfix.rules._base import FunctionCtx, make_diagnostic, rule
from pydocfix.rules.helpers import detect_section_indent
from pydocfix.rules.prm.helpers import (
    bare_name,
    get_documented_param_nodes,
    get_signature_params,
    is_param_section,
)


def _build_stub(name: str, ann: str | None, *, is_numpy: bool, indent: str) -> str:
    """Build a stub entry string for a missing parameter."""
    if is_numpy:
        header = f"{indent}{name} : {ann}" if ann else f"{indent}{name}"
        return f"\n{header}"
    if ann:
        return f"\n{indent}{name} ({ann}):"
    return f"\n{indent}{name}:"


@rule("PRM004", targets=FunctionCtx, cst_types=(GoogleSection, NumPySection))
def prm004(node: GoogleSection | NumPySection, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Docstring has Args/Parameters section but is missing documented parameters."""
    section = node
    if not is_param_section(section):
        return

    documented = {bare_name(name) for name, _ in get_documented_param_nodes(ctx.docstring_cst, section)}
    sig_params = get_signature_params(ctx.parent)

    if not documented:
        return

    is_numpy = isinstance(section, NumPySection)
    section_indent = detect_section_indent(ctx.docstring_text, ctx.docstring_stmt.col_offset)
    indent = section_indent + "    "
    insert_offset = section.range.end

    for display_name, ann in sig_params:
        if bare_name(display_name) in documented:
            continue
        stub = _build_stub(display_name, ann, is_numpy=is_numpy, indent=indent)
        fix = Fix(
            edits=[insert_at(insert_offset, stub)],
            applicability=Applicability.UNSAFE,
        )
        message = f"Missing parameter '{display_name}' in docstring."
        yield make_diagnostic("PRM004", ctx, message, fix=fix, target=section.header_name or section)
