"""Rule DOC003 - One-line docstring should be written on a single line."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import PlainDocstring

from pydocfix._types import Applicability, Diagnostic, Edit, Fix
from pydocfix.rules._base import BaseRule, DiagnoseContext


class DOC003(BaseRule[PlainDocstring]):
    """One-line docstring should be written on a single line."""

    code = "DOC003"
    enabled_by_default = True

    def diagnose(
        self,
        node: PlainDocstring,
        ctx: DiagnoseContext,
    ) -> Iterator[Diagnostic]:
        root = node

        # Must be a multiline docstring
        if "\n" not in ctx.docstring_text:
            return

        # Must have a summary
        if root.summary is None:
            return

        # Docstring must have exactly one non-empty line (the summary).
        # Multiple non-empty lines mean a multi-line summary or extra content.
        if sum(1 for line in ctx.docstring_text.splitlines() if line.strip()) != 1:
            return

        summary_text = root.summary.text.strip()
        if not summary_text:
            return

        content_bytes = ctx.docstring_text.encode("utf-8")
        fix = Fix(
            edits=[Edit(start=0, end=len(content_bytes), new_text=summary_text)],
            applicability=Applicability.SAFE,
        )
        yield self._make_diagnostic(
            ctx,
            "One-line docstring should be written on a single line.",
            fix=fix,
            target=root.summary,
        )
