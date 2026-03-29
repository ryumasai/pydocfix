"""Rule PRM006 - Docstring parameters are in a different order than the signature."""

from __future__ import annotations

import ast
from collections.abc import Iterator

import pydocstring
from pydocstring import (
    GoogleArg,
    GoogleSection,
    GoogleSectionKind,
    NumPySection,
    NumPySectionKind,
    Visitor,
)

from pydocfix.rules._base import Applicability, BaseRule, DiagnoseContext, Diagnostic, Edit, Fix


def _bare_name(name: str) -> str:
    """Strip leading ``*`` or ``**`` from a parameter name."""
    return name.lstrip("*")


class PRM006(BaseRule):
    """Docstring parameters are listed in a different order than the function signature."""

    code = "PDX-PRM006"
    message = "Docstring parameters are not in the same order as the function signature."
    target_kinds = {
        GoogleSection,
        NumPySection,
    }

    @staticmethod
    def _is_param_section(section) -> bool:
        if isinstance(section, GoogleSection):
            return section.section_kind == GoogleSectionKind.ARGS
        if isinstance(section, NumPySection):
            return section.section_kind == NumPySectionKind.PARAMETERS
        return False

    @staticmethod
    def _get_documented_param_nodes(parsed, section) -> list[tuple[str, object]]:
        """Return ``(bare_name, node)`` pairs for each documented parameter, in order."""
        result: list[tuple[str, object]] = []

        class _Collector(Visitor):
            def enter_google_arg(self, node, ctx):
                if node.range.start >= section.range.start and node.range.end <= section.range.end and node.name:
                    result.append((_bare_name(node.name.text), node))

            def enter_numpy_parameter(self, node, ctx):
                if node.range.start >= section.range.start and node.range.end <= section.range.end and node.names:
                    result.append((_bare_name(node.names[0].text), node))

        pydocstring.walk(parsed, _Collector())
        return result

    @staticmethod
    def _get_signature_order(func: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
        """Return bare parameter names in signature order, excluding ``self``/``cls``."""
        result: list[str] = []
        all_positional = [*func.args.posonlyargs, *func.args.args]
        skip_first = bool(all_positional) and all_positional[0].arg in ("self", "cls")
        for i, arg in enumerate(all_positional):
            if i == 0 and skip_first:
                continue
            result.append(arg.arg)
        for arg in func.args.kwonlyargs:
            result.append(arg.arg)
        if func.args.vararg:
            result.append(func.args.vararg.arg)
        if func.args.kwarg:
            result.append(func.args.kwarg.arg)
        return result

    @staticmethod
    def _entry_span(ds_bytes: bytes, param_node) -> tuple[int, int]:
        """Return ``(start, end)`` byte positions for a full parameter entry."""
        nl_before = ds_bytes.rfind(b"\n", 0, param_node.range.start)
        start = nl_before + 1 if nl_before != -1 else param_node.range.start
        nl_after = ds_bytes.find(b"\n", param_node.range.end)
        end = nl_after + 1 if nl_after != -1 else param_node.range.end
        return start, end

    def _build_reorder_fix(
        self,
        ds_text: str,
        doc_params: list[tuple[str, object]],
        sig_order: list[str],
    ) -> Fix:
        ds_bytes = ds_text.encode("utf-8")
        entries = [(name, *self._entry_span(ds_bytes, node)) for name, node in doc_params]
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

    def diagnose(self, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        section = ctx.target_cst
        if not isinstance(section, (GoogleSection, NumPySection)):
            return
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return
        if not self._is_param_section(section):
            return

        doc_params = self._get_documented_param_nodes(ctx.docstring_cst, section)
        sig_order = self._get_signature_order(ctx.parent_ast)

        sig_set = set(sig_order)
        doc_names = [name for name, _ in doc_params if name in sig_set]
        doc_name_set = set(doc_names)
        expected = [name for name in sig_order if name in doc_name_set]

        if doc_names == expected:
            return

        fix = self._build_reorder_fix(ctx.docstring_text, doc_params, sig_order)

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
            yield self._make_diagnostic(
                ctx,
                message,
                fix=fix if first else None,
                target=name_token or param_node,
            )
            first = False
