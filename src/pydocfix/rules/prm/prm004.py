"""Rule PRM004 - Missing parameter in docstring."""

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

from pydocfix.rules._base import Applicability, BaseRule, DiagnoseContext, Diagnostic, Fix, insert_at


def _bare_name(name: str) -> str:
    """Strip leading ``*`` or ``**`` from a parameter name."""
    return name.lstrip("*")


class PRM004(BaseRule):
    """Docstring has Args/Parameters section but is missing documented parameters."""

    code = "PDX-PRM004"
    message = "Missing parameter in docstring."
    target_kinds = {
        GoogleSection,
        NumPySection,
    }

    # -- helpers -------------------------------------------------------

    @staticmethod
    def _is_param_section(section: GoogleSection | NumPySection) -> bool:
        """Return True if *section* is a parameter section."""
        if isinstance(section, GoogleSection):
            return section.section_kind == GoogleSectionKind.ARGS
        return section.section_kind == NumPySectionKind.PARAMETERS

    @staticmethod
    def _get_documented_params(parsed, section: GoogleSection | NumPySection) -> set[str]:
        """Extract bare parameter names documented in the section."""
        names: set[str] = set()

        class _ParamCollector(Visitor):
            def enter_google_arg(self, node, ctx):
                if node.range.start >= section.range.start and node.range.end <= section.range.end and node.name:
                    names.add(_bare_name(node.name.text))

            def enter_numpy_parameter(self, node, ctx):
                if node.range.start >= section.range.start and node.range.end <= section.range.end:
                    for n in node.names:
                        names.add(_bare_name(n.text))

        pydocstring.walk(parsed, _ParamCollector())
        return names

    @staticmethod
    def _get_signature_params(
        func: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> list[tuple[str, str | None]]:
        """Return ``(display_name, annotation_or_None)`` for each parameter, excluding ``self``/``cls``."""
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
    def _build_stub(name: str, ann: str | None, *, is_numpy: bool, indent: str) -> str:
        """Build a stub entry string for a missing parameter."""
        if is_numpy:
            header = f"{indent}{name} : {ann}" if ann else f"{indent}{name}"
            return f"\n{header}"
        if ann:
            return f"\n{indent}{name} ({ann}):"
        return f"\n{indent}{name}:"

    # -- entry point ---------------------------------------------------

    def diagnose(self, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        section = ctx.target_cst
        if not isinstance(section, (GoogleSection, NumPySection)):
            return
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return
        if not self._is_param_section(section):
            return

        documented = self._get_documented_params(ctx.docstring_cst, section)
        sig_params = self._get_signature_params(ctx.parent_ast)

        if not documented:
            return

        is_numpy = isinstance(section, NumPySection)
        indent = "    "
        insert_offset = section.range.end

        for display_name, ann in sig_params:
            if _bare_name(display_name) in documented:
                continue
            stub = self._build_stub(display_name, ann, is_numpy=is_numpy, indent=indent)
            fix = Fix(
                edits=[insert_at(insert_offset, stub)],
                applicability=Applicability.UNSAFE,
            )
            message = f"Missing parameter '{display_name}' in docstring."
            yield self._make_diagnostic(ctx, message, fix=fix, target=section.header_name or section)
