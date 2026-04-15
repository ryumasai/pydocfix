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


class DOC001(BaseRule[GoogleDocstring | NumPyDocstring]):
    """Docstring sections are not in canonical order."""

    code = "DOC001"
    enabled_by_default = True

    def diagnose(self, node: GoogleDocstring | NumPyDocstring, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        root = node
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

        # Build a single Edit covering the entire section block
        # (from the first section's start to the last section's end).
        #
        # For each section, only its "clean" text (up to the last entry-depth
        # line) is moved.  Any trailing content absorbed by the parser at
        # shallower indent (stray lines without a blank-line separator) stays
        # at its original byte position by being included in the inter-section
        # gap rather than travelling with the section.
        #
        # Using one Edit instead of per-slot edits ensures DOC001's edit
        # geometrically overlaps any edit from other rules (e.g. RIS005) that
        # touch the same section block, so that the overlap detector serialises
        # them across iterations rather than applying both simultaneously.
        n = len(sections)
        # clean_end byte (absolute) for each section: end of last entry-depth line
        clean_ends = [
            sections[i].range.start + _section_clean_end(ds_bytes[sections[i].range.start : sections[i].range.end])
            for i in range(n)
        ]
        # Gaps between sections: from clean_end[i] to sections[i+1].range.start
        gaps = [
            ds_bytes[clean_ends[i] : sections[i + 1].range.start].decode("utf-8")
            for i in range(n - 1)
        ]

        # Reconstruct the full section block in sorted order, preserving gaps.
        parts: list[str] = []
        for i, src_section in enumerate(sorted_sections):
            src_bytes = ds_bytes[src_section.range.start : src_section.range.end]
            clean_len = _section_clean_end(src_bytes)
            parts.append(src_bytes[:clean_len].decode("utf-8"))
            if i < n - 1:
                parts.append(gaps[i])

        new_text = "".join(parts)
        fix = Fix(
            edits=[Edit(start=sections[0].range.start, end=sections[-1].range.end, new_text=new_text)],
            applicability=Applicability.UNSAFE,
        )

        # Report at the first section whose position differs from the sorted
        # order, so the user can see exactly where the disorder begins.
        first_wrong = next(
            sections[i] for i, (actual, expected) in enumerate(zip(sections, sorted_sections)) if actual is not expected
        )
        yield self._make_diagnostic(ctx, "Docstring sections are not in canonical order.", fix=fix, target=first_wrong)
