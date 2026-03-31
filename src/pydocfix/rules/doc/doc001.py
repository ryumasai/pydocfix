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


def _section_clean_end(section_bytes: bytes) -> int:
    """Return the byte offset within *section_bytes* of the end of the last entry-level line.

    Under Google/NumPy style, entry lines are indented deeper than the section
    header line (which is at offset 0 within *section_bytes*).  Content that
    appears after the last entry-depth line but is shallower than entry depth is
    "stray" text that was absorbed into the section range by the parser.

    We exclude that trailing stray content by returning the position just after
    the last line whose indent equals the maximum across all non-header,
    non-blank lines.
    """
    lines = section_bytes.split(b"\n")
    if len(lines) <= 1:
        return len(section_bytes)

    # Find the maximum indent depth among non-blank, non-header lines.
    max_indent = 0
    for line in lines[1:]:
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(b" \t"))
        if indent > max_indent:
            max_indent = indent

    if max_indent == 0:
        # No entries found; keep only the header line.
        return len(lines[0])

    # Walk lines again to find the byte position after the *last* line at
    # max_indent (or deeper — for continuation text).
    clean_end = len(lines[0])  # at minimum, keep the header
    pos = len(lines[0])
    for line in lines[1:]:
        pos += 1  # newline separator
        line_end = pos + len(line)
        if line.strip():
            indent = len(line) - len(line.lstrip(b" \t"))
            if indent >= max_indent:
                clean_end = line_end
        pos = line_end

    return clean_end


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

        # Sort sections by canonical order; for equal keys (e.g. two UNKNOWN
        # sections), preserve their original relative order via the enumerate
        # index.
        sorted_indexed = sorted(
            enumerate(sections),
            key=lambda x: (_order_key(x[1].section_kind, order), x[0]),
        )
        sorted_sections = [s for _, s in sorted_indexed]

        # Reorder by swapping the "clean" section texts in-place.
        # Each slot sections[i] is replaced only up to its own clean_end
        # (the end of its last entry-depth line).  Any trailing content at
        # shallower indent ("stray" lines absorbed into the section range by
        # the parser) is left untouched in the gap, preventing it from being
        # moved to a different section where other rules might misinterpret it.
        edits = []
        for i in range(len(sections)):
            if sections[i] is sorted_sections[i]:
                continue
            src_section = sorted_sections[i]
            src_bytes = ds_bytes[src_section.range.start : src_section.range.end]
            clean_len = _section_clean_end(src_bytes)
            new_text = src_bytes[:clean_len].decode("utf-8")

            # Replace only the clean part of the target slot; any stray
            # trailing content in sections[i] is left at its byte position.
            tgt_section = sections[i]
            tgt_bytes = ds_bytes[tgt_section.range.start : tgt_section.range.end]
            tgt_clean_end = tgt_section.range.start + _section_clean_end(tgt_bytes)
            edits.append(
                Edit(
                    start=tgt_section.range.start,
                    end=tgt_clean_end,
                    new_text=new_text,
                )
            )

        fix = Fix(edits=edits, applicability=Applicability.UNSAFE)

        # Report at the first section whose position differs from the sorted
        # order, so the user can see exactly where the disorder begins.
        first_wrong = next(
            sections[i] for i, (actual, expected) in enumerate(zip(sections, sorted_sections)) if actual is not expected
        )
        yield self._make_diagnostic(ctx, self.message, fix=fix, target=first_wrong)
