"""Rule PRM004 - Missing parameter in docstring."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import (
    GoogleSection,
    NumPySection,
)

from pydocfix.rules._base import Applicability, BaseRule, DiagnoseContext, Diagnostic, Fix, insert_at
from pydocfix.rules.prm._helpers import (
    bare_name,
    get_documented_param_nodes,
    get_signature_params,
    is_param_section,
)


class PRM004(BaseRule[GoogleSection | NumPySection]):
    """Docstring has Args/Parameters section but is missing documented parameters."""

    code = "PRM004"

    # -- helpers -------------------------------------------------------

    @staticmethod
    def _build_stub(name: str, ann: str | None, *, is_numpy: bool, indent: str) -> str:
        """Build a stub entry string for a missing parameter."""
        if is_numpy:
            header = f"{indent}{name} : {ann}" if ann else f"{indent}{name}"
            return f"\n{header}"
        if ann:
            return f"\n{indent}{name} ({ann}):"
        return f"\n{indent}{name}:"

    # -- entry point ---------------------------------------------------

    def diagnose(self, node: GoogleSection | NumPySection, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        section = node
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return
        if not is_param_section(section):
            return

        documented = {bare_name(name) for name, _ in get_documented_param_nodes(ctx.docstring_cst, section)}
        sig_params = get_signature_params(ctx.parent_ast)

        if not documented:
            return

        is_numpy = isinstance(section, NumPySection)
        indent = "    "
        insert_offset = section.range.end

        for display_name, ann in sig_params:
            if bare_name(display_name) in documented:
                continue
            stub = self._build_stub(display_name, ann, is_numpy=is_numpy, indent=indent)
            fix = Fix(
                edits=[insert_at(insert_offset, stub)],
                applicability=Applicability.UNSAFE,
            )
            message = f"Missing parameter '{display_name}' in docstring."
            yield self._make_diagnostic(ctx, message, fix=fix, target=section.header_name or section)
