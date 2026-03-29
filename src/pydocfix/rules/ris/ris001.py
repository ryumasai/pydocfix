"""Rule RIS001 - Function raises exceptions but docstring has no Raises section."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import (
    GoogleDocstring,
    GoogleSectionKind,
    NumPyDocstring,
    NumPySectionKind,
    PlainDocstring,
)

from pydocfix.rules._base import Applicability, BaseRule, DiagnoseContext, Diagnostic, Fix, insert_at
from pydocfix.rules.ris._helpers import get_raised_exceptions


class RIS001(BaseRule):
    """Function has raise statements but docstring has no Raises section."""

    code = "PDX-RIS001"
    message = "Missing Raises section in docstring."
    target_kinds = {
        GoogleDocstring,
        NumPyDocstring,
        PlainDocstring,
    }

    @staticmethod
    def _has_raises_section(root) -> bool:
        if isinstance(root, PlainDocstring):
            return False
        for sec in root.sections:
            if isinstance(root, GoogleDocstring):
                if sec.section_kind == GoogleSectionKind.RAISES:
                    return True
            else:
                if sec.section_kind == NumPySectionKind.RAISES:
                    return True
        return False

    @staticmethod
    def _detect_indent(ds_text: str, root) -> str:
        """Guess indentation from existing sections, defaulting to 4 spaces."""
        return "    "

    @staticmethod
    def _build_stub(exc_names: list[str], *, is_numpy: bool, indent: str) -> str:
        lines: list[str] = []
        if is_numpy:
            lines.append("Raises")
            lines.append("------")
            for name in exc_names:
                lines.append(name)
        else:
            lines.append("Raises:")
            for name in exc_names:
                lines.append(f"{indent}{name}:")
        return "\n".join(lines)

    def diagnose(self, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        root = ctx.target_cst
        if not isinstance(root, (GoogleDocstring, NumPyDocstring, PlainDocstring)):
            return
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        raised = get_raised_exceptions(ctx.parent_ast)
        if not raised:
            return

        if self._has_raises_section(root):
            return

        is_numpy = isinstance(root, NumPyDocstring)
        indent = self._detect_indent(ctx.docstring_text, root)
        stub = self._build_stub(raised, is_numpy=is_numpy, indent=indent)

        fix = Fix(
            edits=[insert_at(root.range.end, f"\n\n{stub}\n")],
            applicability=Applicability.UNSAFE,
        )
        summary_token = root.summary
        yield self._make_diagnostic(ctx, self.message, fix=fix, target=summary_token or root)
