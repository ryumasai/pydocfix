"""Rule PRM001 - Function has parameters but docstring has no Args/Parameters section."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import (
    GoogleDocstring,
    NumPyDocstring,
    PlainDocstring,
)

from pydocfix.rules._base import (
    Applicability,
    BaseRule,
    DiagnoseContext,
    Diagnostic,
    Fix,
    detect_section_indent,
    section_append_edit,
)
from pydocfix.rules.prm._helpers import get_signature_params, is_param_section


class PRM001(BaseRule):
    """Function has parameters but docstring has no Args/Parameters section."""

    code = "PDX-PRM001"
    message = "Missing Args/Parameters section in docstring."
    target_kinds = {
        GoogleDocstring,
        NumPyDocstring,
        PlainDocstring,
    }

    # -- helpers -------------------------------------------------------

    @staticmethod
    def _build_stub(params: list[tuple[str, str | None]], *, is_numpy: bool, section_indent: str) -> str:
        entry_indent = section_indent + "    "
        lines: list[str] = []
        if is_numpy:
            lines.append(f"{section_indent}Parameters")
            lines.append(f"{section_indent}----------")
            for name, ann in params:
                if ann:
                    lines.append(f"{section_indent}{name} : {ann}")
                else:
                    lines.append(f"{section_indent}{name}")
        else:
            lines.append(f"{section_indent}Args:")
            for name, ann in params:
                if ann:
                    lines.append(f"{entry_indent}{name} ({ann}):")
                else:
                    lines.append(f"{entry_indent}{name}:")
        return "\n".join(lines)

    def diagnose(self, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        root = ctx.target_cst
        if not isinstance(root, (GoogleDocstring, NumPyDocstring, PlainDocstring)):
            return
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        sig_params = get_signature_params(ctx.parent_ast)
        if not sig_params:
            return
        if isinstance(root, PlainDocstring):
            # Plain docstrings never have sections
            pass
        elif any(is_param_section(sec) for sec in root.sections):
            return

        is_numpy = isinstance(root, NumPyDocstring)
        section_indent = detect_section_indent(ctx.docstring_text, ctx.docstring_stmt.col_offset)
        stub = self._build_stub(sig_params, is_numpy=is_numpy, section_indent=section_indent)

        fix = Fix(
            edits=[section_append_edit(ctx.docstring_text, root.range.end, stub)],
            applicability=Applicability.UNSAFE,
        )
        summary_token = root.summary
        yield self._make_diagnostic(ctx, self.message, fix=fix, target=summary_token or root)
