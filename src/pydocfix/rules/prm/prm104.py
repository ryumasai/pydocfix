"""Rule PRM104 - Parameter has no type in docstring."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleArg, NumPyParameter

from pydocfix.rules._base import Applicability, BaseRule, DiagnoseContext, Diagnostic, Edit, Fix


class PRM104(BaseRule):
    """Docstring parameter has no type annotation (type_annotation_style = "docstring")."""

    code = "PDX-PRM104"
    message = "Parameter has no type in docstring."
    enabled_by_default = False
    target_kinds = {
        GoogleArg,
        NumPyParameter,
    }

    @staticmethod
    def _get_annotation(func: ast.FunctionDef | ast.AsyncFunctionDef, bare_name: str) -> str | None:
        for arg in (*func.args.args, *func.args.posonlyargs, *func.args.kwonlyargs):
            if arg.arg == bare_name and arg.annotation is not None:
                return ast.unparse(arg.annotation)
        if func.args.vararg and func.args.vararg.arg == bare_name and func.args.vararg.annotation is not None:
            return ast.unparse(func.args.vararg.annotation)
        if func.args.kwarg and func.args.kwarg.arg == bare_name and func.args.kwarg.annotation is not None:
            return ast.unparse(func.args.kwarg.annotation)
        return None

    def _build_insert_type_fix(self, cst_node, ann: str, ds_text: str) -> Fix:
        """Build a fix that inserts the type annotation into the docstring entry."""
        if isinstance(cst_node, GoogleArg):
            name_token = cst_node.name
            if name_token is None:
                return Fix(edits=[], applicability=Applicability.UNSAFE)
            insert_pos = name_token.range.end
            return Fix(
                edits=[Edit(start=insert_pos, end=insert_pos, new_text=f" ({ann})")],
                applicability=Applicability.UNSAFE,
            )
        else:  # NumPyParameter
            name_token = cst_node.names[0] if cst_node.names else None
            if name_token is None:
                return Fix(edits=[], applicability=Applicability.UNSAFE)
            if cst_node.colon:
                insert_pos = cst_node.colon.range.end
                return Fix(
                    edits=[Edit(start=insert_pos, end=insert_pos, new_text=f" {ann}")],
                    applicability=Applicability.UNSAFE,
                )
            else:
                insert_pos = name_token.range.end
                return Fix(
                    edits=[Edit(start=insert_pos, end=insert_pos, new_text=f" : {ann}")],
                    applicability=Applicability.UNSAFE,
                )

    def diagnose(self, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = ctx.target_cst
        if not isinstance(cst_node, (GoogleArg, NumPyParameter)):
            return
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        if isinstance(cst_node, GoogleArg):
            name_token = cst_node.name
            type_token = cst_node.type
        else:
            name_token = cst_node.names[0] if cst_node.names else None
            type_token = cst_node.type
        if name_token is None:
            return
        if type_token is not None and type_token.text.strip():
            return

        bare_name = name_token.text.lstrip("*")
        ann = self._get_annotation(ctx.parent_ast, bare_name)
        fix = None
        if ann:
            fix = self._build_insert_type_fix(cst_node, ann, ctx.docstring_text)

        message = f"Parameter \'{name_token.text}\' has no type in docstring."
        yield self._make_diagnostic(ctx, message, fix=fix, target=name_token)
