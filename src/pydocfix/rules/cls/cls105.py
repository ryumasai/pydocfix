"""Rule CLS105 - Class docstring missing Args section (style='class')."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleDocstring, GoogleSectionKind, NumPyDocstring, NumPySectionKind, PlainDocstring

from pydocfix.diagnostics import Applicability, Diagnostic, Fix
from pydocfix.fixes import section_append_edit
from pydocfix.rules._base import ActivationCondition, ClassCtx, make_diagnostic, rule
from pydocfix.rules.cls.helpers import get_init_method
from pydocfix.rules.helpers import build_section_stub, detect_docstring_style, detect_section_indent, has_section
from pydocfix.rules.prm.helpers import get_signature_params


@rule(
    "CLS105",
    targets=ClassCtx,
    cst_types=(GoogleDocstring, NumPyDocstring, PlainDocstring),
    enabled_by_default=False,
    activation_condition=ActivationCondition("class_docstring_style", frozenset({"class"})),
)
def cls105(node: GoogleDocstring | NumPyDocstring | PlainDocstring, ctx: ClassCtx) -> Iterator[Diagnostic]:
    """Class docstring is missing an Args/Parameters section but class_docstring_style is 'class'."""
    if ctx.config is None or ctx.config.class_docstring_style != "class":
        return

    root = node
    if isinstance(root, PlainDocstring) and (ctx.config is None or ctx.config.skip_short_docstrings):
        return

    if not isinstance(root, PlainDocstring) and has_section(root, GoogleSectionKind.ARGS, NumPySectionKind.PARAMETERS):
        return

    # Find __init__ to get its parameters
    init_method = get_init_method(ctx.parent)
    if init_method is None:
        return
    sig_params = get_signature_params(init_method)
    if not sig_params:
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
        "CLS105",
        ctx,
        "Class docstring is missing an Args/Parameters section (class_docstring_style is 'class').",
        fix=fix,
        target=summary_token or root,
    )
