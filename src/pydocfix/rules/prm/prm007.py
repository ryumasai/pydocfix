"""Rule PRM007 - Duplicate parameter in docstring."""

from __future__ import annotations

import ast
from collections.abc import Iterator

import pydocstring
from pydocstring import (
    GoogleSection,
    GoogleSectionKind,
    NumPySection,
    NumPySectionKind,
    Visitor,
)

from pydocfix.rules._base import (
    Applicability,
    BaseRule,
    DiagnoseContext,
    Diagnostic,
    Fix,
    delete_range,
)


class PRM007(BaseRule):
    """Docstring documents a parameter more than once."""

    code = "PDX-PRM007"
    message = "Duplicate parameter in docstring."
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
    def _build_delete_fix(ds_text: str, param_node) -> Fix:
        ds_bytes = ds_text.encode("utf-8")
        nl_before = ds_bytes.rfind(b"\n", 0, param_node.range.start)
        start = nl_before + 1 if nl_before != -1 else param_node.range.start
        nl_after = ds_bytes.find(b"\n", param_node.range.end)
        end = nl_after + 1 if nl_after != -1 else param_node.range.end
        return Fix(
            edits=[delete_range(start, end)],
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

        # Collect all param entries in this section via walk
        entries: list[tuple[str, object, object]] = []  # (name, node, name_token)

        class _Collector(Visitor):
            def enter_google_arg(self, node, walk_ctx):
                if node.range.start >= section.range.start and node.range.end <= section.range.end and node.name:
                    entries.append((node.name.text, node, node.name))

            def enter_numpy_parameter(self, node, walk_ctx):
                if node.range.start >= section.range.start and node.range.end <= section.range.end and node.names:
                    entries.append((node.names[0].text, node, node.names[0]))

        pydocstring.walk(ctx.docstring_cst, _Collector())

        seen: set[str] = set()
        for name, param_node, name_token in entries:
            if name in seen:
                fix = self._build_delete_fix(ctx.docstring_text, param_node)
                message = f"Parameter '{name}' is documented more than once."
                yield self._make_diagnostic(ctx, message, fix=fix, target=name_token)
            else:
                seen.add(name)
