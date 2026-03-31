"""Rule PRM001 - Function has parameters but docstring has no Args/Parameters section."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import (
    GoogleDocstring,
    NumPyDocstring,
    PlainDocstring,
)

from pydocfix.rules._base import Applicability, BaseRule, DiagnoseContext, Diagnostic, Fix, insert_at
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
    def _build_stub(params: list[tuple[str, str | None]], *, is_numpy: bool, indent: str) -> str:
        lines: list[str] = []
        if is_numpy:
            lines.append("Parameters")
            lines.append("----------")
            for name, ann in params:
                if ann:
                    lines.append(f"{name} : {ann}")
                else:
                    lines.append(name)
        else:
            lines.append("Args:")
            for name, ann in params:
                if ann:
                    lines.append(f"{indent}{name} ({ann}):")
                else:
                    lines.append(f"{indent}{name}:")
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
        indent = "    "
        stub = self._build_stub(sig_params, is_numpy=is_numpy, indent=indent)

        fix = Fix(
            edits=[insert_at(root.range.end, f"\n\n{stub}\n")],
            applicability=Applicability.UNSAFE,
        )
        summary_token = root.summary
        yield self._make_diagnostic(ctx, self.message, fix=fix, target=summary_token or root)
