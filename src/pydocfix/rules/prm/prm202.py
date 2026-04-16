"""Rule PRM202 - Parameter with default value missing ``default`` in docstring."""

from __future__ import annotations

import ast
import re
from collections.abc import Iterator

from pydocstring import GoogleArg, NumPyParameter

from pydocfix.rules._base import Applicability, BaseRule, DiagnoseContext, Diagnostic, Edit, Fix
from pydocfix.rules.prm._helpers import bare_name, get_param_name_token

_DEFAULT_RE = re.compile(r"\bdefault[s]?\b", re.IGNORECASE)


class PRM202(BaseRule[GoogleArg | NumPyParameter]):
    """Parameter has a default value but docstring does not mention ``default``."""

    code = "PRM202"
    enabled_by_default = False

    @staticmethod
    def _get_default_values(func: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, str]:
        """Return mapping of bare parameter name -> repr of default value."""
        result: dict[str, str] = {}
        n_args = len(func.args.args)
        n_defaults = len(func.args.defaults)
        for i, arg in enumerate(func.args.args):
            di = i - (n_args - n_defaults)
            if di >= 0:
                result[arg.arg] = ast.unparse(func.args.defaults[di])
        for arg, default in zip(func.args.kwonlyargs, func.args.kw_defaults, strict=False):
            if default is not None:
                result[arg.arg] = ast.unparse(default)
        return result

    def _has_default_mention(self, cst_node) -> bool:
        r"""Check if the docstring entry already mentions 'default'."""
        # NumPy style: check for default_keyword
        if isinstance(cst_node, NumPyParameter) and cst_node.default_keyword is not None:
            return True
        # Also check in description text
        desc = cst_node.description
        return bool(desc and _DEFAULT_RE.search(desc.text))

    def diagnose(self, node: GoogleArg | NumPyParameter, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        cst_node = node
        if not isinstance(ctx.parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return

        name_token = get_param_name_token(cst_node)
        if name_token is None:
            return

        b = bare_name(name_token.text)
        default_values = self._get_default_values(ctx.parent_ast)
        if b not in default_values:
            return

        if self._has_default_mention(cst_node):
            return

        default_repr = default_values[b]
        desc = cst_node.description
        fix = None
        if desc:
            text = desc.text.rstrip()
            suffix = "" if text.endswith(".") else "."
            insert_text = f"{suffix} Defaults to {default_repr}."
            fix = Fix(
                edits=[Edit(start=desc.range.end, end=desc.range.end, new_text=insert_text)],
                applicability=Applicability.UNSAFE,
            )

        message = f"Parameter '{name_token.text}' has default value but docstring does not mention 'default'."
        yield self._make_diagnostic(ctx, message, fix=fix, target=name_token)
