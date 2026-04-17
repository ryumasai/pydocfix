"""Rule DOC003 - One-line docstring should be written on a single line."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import GoogleDocstring, NumPyDocstring, PlainDocstring

from pydocfix.rules._base import Applicability, BaseRule, DiagnoseContext, Diagnostic, Edit, Fix


class DOC003(BaseRule[GoogleDocstring | NumPyDocstring | PlainDocstring]):
    """One-line docstring should be written on a single line."""

    code = "DOC003"
    enabled_by_default = True

    def diagnose(
        self,
        node: GoogleDocstring | NumPyDocstring | PlainDocstring,
        ctx: DiagnoseContext,
    ) -> Iterator[Diagnostic]:
        root = node

        # Must be a multiline docstring
        if "\n" not in ctx.docstring_text:
            return

        # Must have a non-empty summary
        if root.summary is None:
            return
        summary_text = root.summary.text.strip()
        if not summary_text:
            return

        # Summary itself must be single-line
        if "\n" in summary_text:
            return

        # Must have no sections (sections require multiline format)
        if getattr(root, "sections", []):
            return

        # Must have no extended summary (content beyond the summary line)
        remaining = ctx.docstring_text.encode("utf-8")[root.summary.range.end :]
        if remaining.strip():
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
