"""Rule DOC001 - Docstring sections are not in canonical order."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Final

from pydocstring import (
    GoogleDocstring,
    GoogleSectionKind,
    NumPyDocstring,
    NumPySectionKind,
)

from pydocfix.rules._base import (
    Applicability,
    BaseRule,
    DiagnoseContext,
    Diagnostic,
    Edit,
    Fix,
)

# Canonical section order for Google-style docstrings.
# Sections not in this list (UNKNOWN) sort to the end.
_GOOGLE_ORDER: Final[list] = [
    GoogleSectionKind.ARGS,
    GoogleSectionKind.KEYWORD_ARGS,
    GoogleSectionKind.OTHER_PARAMETERS,
    GoogleSectionKind.RECEIVES,
    GoogleSectionKind.RETURNS,
    GoogleSectionKind.YIELDS,
    GoogleSectionKind.RAISES,
    GoogleSectionKind.WARNS,
    GoogleSectionKind.ATTRIBUTES,
    GoogleSectionKind.METHODS,
    GoogleSectionKind.NOTES,
    GoogleSectionKind.REFERENCES,
    GoogleSectionKind.EXAMPLES,
    GoogleSectionKind.SEE_ALSO,
    GoogleSectionKind.TODO,
    GoogleSectionKind.HINT,
    GoogleSectionKind.TIP,
    GoogleSectionKind.IMPORTANT,
    GoogleSectionKind.ATTENTION,
    GoogleSectionKind.CAUTION,
    GoogleSectionKind.DANGER,
    GoogleSectionKind.ERROR,
    GoogleSectionKind.WARNINGS,
    GoogleSectionKind.UNKNOWN,
]

# Canonical section order for NumPy-style docstrings.
_NUMPY_ORDER: Final[list] = [
    NumPySectionKind.PARAMETERS,
    NumPySectionKind.OTHER_PARAMETERS,
    NumPySectionKind.RECEIVES,
    NumPySectionKind.RETURNS,
    NumPySectionKind.YIELDS,
    NumPySectionKind.RAISES,
    NumPySectionKind.WARNS,
    NumPySectionKind.ATTRIBUTES,
    NumPySectionKind.METHODS,
    NumPySectionKind.NOTES,
    NumPySectionKind.REFERENCES,
    NumPySectionKind.EXAMPLES,
    NumPySectionKind.SEE_ALSO,
    NumPySectionKind.WARNINGS,
    NumPySectionKind.UNKNOWN,
]


def _order_key(section_kind, order: list) -> int:
    """Return the canonical position of *section_kind*, or len(order) if unknown."""
    try:
        return order.index(section_kind)
    except ValueError:
        return len(order)


class DOC001(BaseRule):
    """Docstring sections are not in canonical order."""

    code = "PDX-DOC001"
    message = "Docstring sections are not in canonical order."
    enabled_by_default = True
    target_kinds = {
        GoogleDocstring,
        NumPyDocstring,
    }

    def diagnose(self, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        root = ctx.target_cst
        if isinstance(root, GoogleDocstring):
            order = _GOOGLE_ORDER
        elif isinstance(root, NumPyDocstring):
            order = _NUMPY_ORDER
        else:
            return

        sections = root.sections
        if len(sections) < 2:
            return  # nothing to reorder

        current_keys = [_order_key(s.section_kind, order) for s in sections]
        sorted_keys = sorted(current_keys)
        if current_keys == sorted_keys:
            return  # already in canonical order

        ds_bytes = ctx.docstring_text.encode("utf-8")

        # Detect the section-level indent from the whitespace that precedes the
        # first section header (everything after the last newline before it).
        first_sec = sections[0]
        prefix = ds_bytes[: first_sec.range.start]
        last_nl = prefix.rfind(b"\n")
        section_indent = prefix[last_nl + 1 :].decode("utf-8") if last_nl != -1 else ""
        separator = f"\n\n{section_indent}"

        # Sort sections by canonical order; for equal keys (e.g. two UNKNOWN
        # sections), preserve their original relative order via the enumerate
        # index.
        sorted_indexed = sorted(
            enumerate(sections),
            key=lambda x: (_order_key(x[1].section_kind, order), x[0]),
        )
        sorted_sections = [s for _, s in sorted_indexed]

        new_text = separator.join(
            ds_bytes[s.range.start : s.range.end].decode("utf-8")
            for s in sorted_sections
        )

        fix = Fix(
            edits=[
                Edit(
                    start=sections[0].range.start,
                    end=sections[-1].range.end,
                    new_text=new_text,
                )
            ],
            applicability=Applicability.UNSAFE,
        )

        # Report at the first section whose position differs from the sorted
        # order, so the user can see exactly where the disorder begins.
        first_wrong = next(
            sections[i]
            for i, (actual, expected) in enumerate(zip(sections, sorted_sections))
            if actual is not expected
        )
        yield self._make_diagnostic(ctx, self.message, fix=fix, target=first_wrong)
