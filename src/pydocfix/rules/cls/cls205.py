"""Rule CLS205 - __init__ docstring missing Args section (style='init')."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleDocstring, GoogleSectionKind, NumPyDocstring, NumPySectionKind, PlainDocstring

from pydocfix.diagnostics import Applicability, Diagnostic, Fix
from pydocfix.fixes import section_append_edit
from pydocfix.rules._base import ActivationCondition, FunctionCtx, make_diagnostic, rule
from pydocfix.rules.helpers import build_section_stub, detect_docstring_style, detect_section_indent, has_section
from pydocfix.rules.prm.helpers import get_signature_params


@rule(
    "CLS205",
    targets=FunctionCtx,
    cst_types=(GoogleDocstring, NumPyDocstring, PlainDocstring),
    enabled_by_default=False,
    activation_condition=ActivationCondition("class_docstring_style", frozenset({"init"})),
)
def cls205(node: GoogleDocstring | NumPyDocstring | PlainDocstring, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """__init__ docstring is missing an Args/Parameters section but class_docstring_style is 'init'."""
    if ctx.config is None or ctx.config.class_docstring_style != "init":
        return
    if ctx.parent.name != "__init__":
        return

    root = node
    if isinstance(root, PlainDocstring) and (ctx.config is None or ctx.config.skip_short_docstrings):
        return

    sig_params = get_signature_params(ctx.parent)
    if not sig_params:
        return

    if not isinstance(root, PlainDocstring) and has_section(root, GoogleSectionKind.ARGS, NumPySectionKind.PARAMETERS):
        return

    style = detect_docstring_style(root, ctx.config)
    section_indent = detect_section_indent(ctx.docstring_text, ctx.docstring_stmt.col_offset)
    stub = build_section_stub("args", style, section_indent, sig_params)

    fix = Fix(
        edits=[section_append_edit(ctx.docstring_text, root.range.end, stub)],
        applicability=Applicability.UNSAFE,
    )
    summary_token = root.summary
    yield make_diagnostic(
        "CLS205",
        ctx,
        "__init__ docstring is missing an Args/Parameters section (class_docstring_style is 'init').",
        fix=fix,
        target=summary_token or root,
    )
