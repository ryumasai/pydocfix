"""Rule PRM006 - Docstring parameters are in a different order than the signature."""

from __future__ import annotations

from collections.abc import Iterator, Sequence

from pydocstring import (
    GoogleArg,
    GoogleSection,
    NumPyParameter,
    NumPySection,
)

from pydocfix.diagnostics import Applicability, Diagnostic, Edit, Fix
from pydocfix.rules._base import FunctionCtx, make_diagnostic, rule
from pydocfix.rules.prm.helpers import (
    bare_name,
    get_documented_param_nodes,
    get_signature_params,
    is_param_section,
)


def _entry_span(ds_bytes: bytes, param_node) -> tuple[int, int]:
    """Return ``(start, end)`` byte positions for a full parameter entry."""
    nl_before = ds_bytes.rfind(b"\n", 0, param_node.range.start)
    start = nl_before + 1 if nl_before != -1 else param_node.range.start
    nl_after = ds_bytes.find(b"\n", param_node.range.end)
    end = nl_after + 1 if nl_after != -1 else param_node.range.end
    return start, end


def _build_reorder_fix(
    ds_text: str,
    doc_params: Sequence[tuple[str, GoogleArg | NumPyParameter]],
    sig_order: list[str],
) -> Fix:
    ds_bytes = ds_text.encode("utf-8")
    entries = [(name, *_entry_span(ds_bytes, node)) for name, node in doc_params]
    sig_index = {name: i for i, name in enumerate(sig_order)}
    sig_set = set(sig_order)
    in_sig = sorted(
        [(name, s, e) for name, s, e in entries if name in sig_set],
        key=lambda x: sig_index[x[0]],
    )
    not_in_sig = [(name, s, e) for name, s, e in entries if name not in sig_set]
    desired = in_sig + not_in_sig
    new_text = "".join(ds_bytes[s:e].decode("utf-8") for _, s, e in desired)
    block_start = entries[0][1]
    block_end = entries[-1][2]
    return Fix(
        edits=[Edit(start=block_start, end=block_end, new_text=new_text)],
        applicability=Applicability.UNSAFE,
    )


@rule("PRM006", ctx_types=frozenset({FunctionCtx}), cst_types=frozenset({GoogleSection, NumPySection}))
def prm006(node: GoogleSection | NumPySection, ctx: FunctionCtx) -> Iterator[Diagnostic]:
    """Docstring parameters are listed in a different order than the function signature."""
    section = node
    if not is_param_section(section):
        return

    doc_params = [(bare_name(name), node) for name, node in get_documented_param_nodes(ctx.docstring_cst, section)]
    sig_order = [bare_name(name) for name, _ in get_signature_params(ctx.parent)]

    sig_set = set(sig_order)
    doc_names = [name for name, _ in doc_params if name in sig_set]
    doc_name_set = set(doc_names)
    expected = [name for name in sig_order if name in doc_name_set]

    if doc_names == expected:
        return

    fix = _build_reorder_fix(ctx.docstring_text, doc_params, sig_order)

    # Filter to only params that exist in the signature for position comparison
    doc_in_sig = [(name, node) for name, node in doc_params if name in sig_set]

    first = True
    for (doc_name, param_node), exp_name in zip(doc_in_sig, expected, strict=False):
        if doc_name == exp_name:
            continue
        if isinstance(param_node, GoogleArg):
            name_token = param_node.name
        else:
            name_token = param_node.names[0] if hasattr(param_node, "names") and param_node.names else None
        message = f"Parameter '{doc_name}' is in the wrong order (expected '{exp_name}' at this position)."
        yield make_diagnostic(
            "PRM006",
            ctx,
            message,
            fix=fix if first else None,
            target=name_token or param_node,
        )
        first = False
