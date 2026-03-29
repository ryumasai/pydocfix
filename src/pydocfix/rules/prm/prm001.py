"""Rule PRM001 - Function has parameters but docstring has no Args/Parameters section."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import (
    GoogleDocstring,
    GoogleSection,
    GoogleSectionKind,
    NumPyDocstring,
    NumPySection,
    NumPySectionKind,
    PlainDocstring,
)

from pydocfix.rules._base import Applicability, BaseRule, DiagnoseContext, Diagnostic, Fix, insert_at


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
    def _get_signature_params(
        func: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> list[tuple[str, str | None]]:
        """Return ``(display_name, annotation_or_None)`` excluding ``self``/``cls``."""
        result: list[tuple[str, str | None]] = []
        all_positional = [*func.args.posonlyargs, *func.args.args]
        skip_first = bool(all_positional) and all_positional[0].arg in ("self", "cls")
        for i, arg in enumerate(all_positional):
            if i == 0 and skip_first:
                continue
            ann = ast.unparse(arg.annotation) if arg.annotation else None
            result.append((arg.arg, ann))
        for arg in func.args.kwonlyargs:
            ann = ast.unparse(arg.annotation) if arg.annotation else None
            result.append((arg.arg, ann))
        if func.args.vararg:
            ann = ast.unparse(func.args.vararg.annotation) if func.args.vararg.annotation else None
            result.append((f"*{func.args.vararg.arg}", ann))
        if func.args.kwarg:
            ann = ast.unparse(func.args.kwarg.annotation) if func.args.kwarg.annotation else None
            result.append((f"**{func.args.kwarg.arg}", ann))
        return result

    @staticmethod
    def _has_param_section(root: GoogleDocstring | NumPyDocstring) -> bool:
        """Return True if the docstring already contains a parameter section."""
        for section in root.sections:
            if isinstance(section, GoogleSection) and section.section_kind == GoogleSectionKind.ARGS:
                return True
            if isinstance(section, NumPySection) and section.section_kind == NumPySectionKind.PARAMETERS:
                return True
        return False

    @staticmethod
    def _detect_indent(ds_text: str, root: GoogleDocstring | NumPyDocstring) -> str:
        """Guess indentation from existing sections or default to 4 spaces."""
        return "    "

    @staticmethod
    def _build_stub(
        params: list[tuple[str, str | None]], *, is_numpy: bool, indent: str
    ) -> str:
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

        sig_params = self._get_signature_params(ctx.parent_ast)
        if not sig_params:
            return
        if isinstance(root, PlainDocstring):
            # Plain docstrings never have sections
            pass
        elif self._has_param_section(root):
            return

        is_numpy = isinstance(root, NumPyDocstring)
        indent = self._detect_indent(ctx.docstring_text, root) if not isinstance(root, PlainDocstring) else "    "
        stub = self._build_stub(sig_params, is_numpy=is_numpy, indent=indent)

        fix = Fix(
            edits=[insert_at(root.range.end, f"\n\n{stub}\n")],
            applicability=Applicability.UNSAFE,
        )
        summary_token = root.summary
        yield self._make_diagnostic(ctx, self.message, fix=fix, target=summary_token or root)
