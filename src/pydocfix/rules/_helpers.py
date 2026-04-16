"""Shared helper functions for all rule categories."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydocstring import (
    GoogleDocstring,
    GoogleSection,
    GoogleSectionKind,
    NumPyDocstring,
    NumPySection,
    NumPySectionKind,
    PlainDocstring,
    TextRange,
)

from pydocfix.rules._base import Applicability, Fix, delete_range

if TYPE_CHECKING:
    from pydocfix.config import Config


def find_section(
    root: GoogleDocstring | NumPyDocstring | PlainDocstring,
    google_kind: GoogleSectionKind | None = None,
    numpy_kind: NumPySectionKind | None = None,
) -> GoogleSection | NumPySection | None:
    """Find a section by kind in a parsed docstring.

    Args:
        root: The parsed docstring (Google, NumPy, or Plain).
        google_kind: The section kind to find in Google-style docstrings.
        numpy_kind: The section kind to find in NumPy-style docstrings.

    Returns:
        The matching section, or None if not found or if root is PlainDocstring.

    Examples:
        >>> find_section(root, GoogleSectionKind.ARGS, NumPySectionKind.PARAMETERS)
        >>> find_section(root, GoogleSectionKind.RETURNS, NumPySectionKind.RETURNS)

    """
    if isinstance(root, PlainDocstring):
        return None

    for sec in root.sections:
        if isinstance(root, GoogleDocstring) and google_kind is not None and sec.section_kind == google_kind:
            return sec
        if isinstance(root, NumPyDocstring) and numpy_kind is not None and sec.section_kind == numpy_kind:
            return sec
    return None


def has_section(
    root: GoogleDocstring | NumPyDocstring | PlainDocstring,
    google_kind: GoogleSectionKind | None = None,
    numpy_kind: NumPySectionKind | None = None,
) -> bool:
    """Check if a section exists in the docstring.

    Args:
        root: The parsed docstring.
        google_kind: The section kind for Google-style.
        numpy_kind: The section kind for NumPy-style.

    Returns:
        True if the section exists, False otherwise.

    """
    return find_section(root, google_kind, numpy_kind) is not None


def delete_section_fix(
    ds_text: str,
    section: GoogleSection | NumPySection,
    applicability: Applicability = Applicability.SAFE,
) -> Fix:
    """Build a Fix that deletes an entire section including surrounding whitespace.

    Args:
        ds_text: The full docstring text.
        section: The section node to delete.
        applicability: The applicability level of the fix.

    Returns:
        A Fix that removes the section and its newline.

    """
    ds_bytes = ds_text.encode("utf-8")
    nl_before = ds_bytes.rfind(b"\n", 0, section.range.start)
    start = nl_before if nl_before != -1 else section.range.start
    nl_after = ds_bytes.find(b"\n", section.range.end)
    end = nl_after + 1 if nl_after != -1 else section.range.end

    return Fix(
        edits=[delete_range(start, end)],
        applicability=applicability,
    )


def delete_entry_fix(ds_text: str, text_range: TextRange, applicability: Applicability) -> Fix:
    """Build a Fix that deletes the full line(s) of a docstring entry node.

    Args:
        ds_text: The full docstring text.
        text_range: The byte-offset range of the entry to delete.
        applicability: The applicability level of the fix.

    Returns:
        A Fix that removes the entry and its newline.

    """
    ds_bytes = ds_text.encode("utf-8")
    nl_before = ds_bytes.rfind(b"\n", 0, text_range.start)
    start = nl_before + 1 if nl_before != -1 else text_range.start
    nl_after = ds_bytes.find(b"\n", text_range.end)
    end = nl_after + 1 if nl_after != -1 else text_range.end
    return Fix(
        edits=[delete_range(start, end)],
        applicability=applicability,
    )


def detect_docstring_style(
    root: GoogleDocstring | NumPyDocstring | PlainDocstring,
    config: Config | None = None,
) -> Literal["google", "numpy"]:
    """Detect whether to use Google or NumPy style for a docstring.

    For GoogleDocstring or NumPyDocstring, returns the corresponding style.
    For PlainDocstring, returns the preferred_style from config (defaulting to "google").

    Args:
        root: The parsed docstring.
        config: Optional configuration object.

    Returns:
        Either "google" or "numpy".

    """
    if isinstance(root, NumPyDocstring):
        return "numpy"
    if isinstance(root, GoogleDocstring):
        return "google"
    # PlainDocstring — use config preference
    if config is not None:
        return config.preferred_style  # type: ignore[return-value]
    return "google"


def build_section_stub(
    section_type: Literal["args", "returns", "yields", "raises"],
    style: Literal["google", "numpy"],
    indent: str,
    entries: list[str] | list[tuple[str, str | None]] | None = None,
) -> str:
    r"""Build a stub section with proper formatting.

    Args:
        section_type: Type of section to build.
        style: Docstring style ("google" or "numpy").
        indent: Base indentation for the section.
        entries: Optional list of entries. Can be:
            - List of strings (for raises, simple yields/returns)
            - List of (name, type) tuples (for args, typed entries)
            - None (for empty sections)

    Returns:
        Formatted section text ready to insert into docstring.

    Examples:
        >>> build_section_stub("args", "google", "    ", [("x", "int"), ("y", None)])
        '    Args:\\n        x (int):\\n        y:'

        >>> build_section_stub("returns", "numpy", "    ", [("int",)])
        '    Returns\\n    -------\\n    int'

        >>> build_section_stub("raises", "google", "    ", ["ValueError", "KeyError"])
        '    Raises:\\n        ValueError:\\n        KeyError:'

    """
    entry_indent = indent + "    "
    lines: list[str] = []

    if style == "numpy":
        # NumPy style headers
        headers = {
            "args": ("Parameters", "----------"),
            "returns": ("Returns", "-------"),
            "yields": ("Yields", "------"),
            "raises": ("Raises", "------"),
        }
        header, underline = headers[section_type]
        lines.append(f"{indent}{header}")
        lines.append(f"{indent}{underline}")

        if entries:
            if section_type == "args":
                # entries: [(name, type), ...]
                for entry in entries:
                    if isinstance(entry, tuple):
                        name, type_hint = entry
                        if type_hint:
                            lines.append(f"{indent}{name} : {type_hint}")
                        else:
                            lines.append(f"{indent}{name}")
                    else:
                        lines.append(f"{indent}{entry}")
            else:
                # entries: [type_or_exception, ...]
                for entry in entries:
                    if isinstance(entry, tuple):
                        lines.append(f"{indent}{entry[0]}")
                    else:
                        lines.append(f"{indent}{entry}")

    else:  # google style
        headers = {
            "args": "Args:",
            "returns": "Returns:",
            "yields": "Yields:",
            "raises": "Raises:",
        }
        lines.append(f"{indent}{headers[section_type]}")

        if entries:
            if section_type == "args":
                # entries: [(name, type), ...]
                for entry in entries:
                    if isinstance(entry, tuple):
                        name, type_hint = entry
                        if type_hint:
                            lines.append(f"{entry_indent}{name} ({type_hint}):")
                        else:
                            lines.append(f"{entry_indent}{name}:")
                    else:
                        lines.append(f"{entry_indent}{entry}:")
            else:
                # entries: [type_or_exception, ...]
                for entry in entries:
                    if isinstance(entry, tuple):
                        lines.append(f"{entry_indent}{entry[0]}:")
                    else:
                        lines.append(f"{entry_indent}{entry}:")

    return "\n".join(lines)
