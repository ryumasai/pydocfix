"""Rule CLS103 - Class docstring has an Args section (style='init')."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from pydocstring import GoogleSection, NumPySection

from pydocfix.diagnostics import Applicability, Diagnostic
from pydocfix.rules._base import ActivationCondition, BaseRule, DiagnoseContext
from pydocfix.rules.cls.helpers import is_param_section
from pydocfix.rules.helpers import delete_section_fix


class CLS103(BaseRule[GoogleSection | NumPySection]):
    """Class docstring has an Args/Parameters section but class_docstring_style is 'init'."""

    code = "CLS103"
    enabled_by_default = False
    activation_condition = ActivationCondition("class_docstring_style", frozenset({"init"}))

    def diagnose(self, node: GoogleSection | NumPySection, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        if self.config is None or self.config.class_docstring_style != "init":
            return
        if not isinstance(ctx.parent_ast, ast.ClassDef):
            return
        if not is_param_section(node):
            return

        fix = delete_section_fix(ctx.docstring_text, node, Applicability.UNSAFE)
        yield self._make_diagnostic(
            ctx,
            "Class docstring should not have an Args/Parameters section when class_docstring_style is 'init'.",
            fix=fix,
            target=node,
        )
