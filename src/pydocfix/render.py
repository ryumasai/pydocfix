"""Diagnostic rendering for pydocfix (ruff-style output)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydocfix.colorize import _BOLD, _DIM, _RED
from pydocfix.colorize import ansi as _ansi

if TYPE_CHECKING:
    from pydocfix.config import Config
    from pydocfix.rules._base import Diagnostic

OutputFormat = Literal["full", "concise"]


def _fix_tag(diag: Diagnostic, config: Config | None, color: bool = True) -> str:
    """Return the fix tag string for a diagnostic (e.g. '[]', '[safe]', '[unsafe]')."""
    from pydocfix.rules._base import Applicability, effective_applicability

    if diag.fix is None:
        return "[]"
    app = effective_applicability(diag, config)
    if app == Applicability.SAFE:
        return "[safe]"
    if app == Applicability.UNSAFE:
        return "[unsafe]"
    if app == Applicability.DISPLAY_ONLY:
        return "[]"
    return "[]"


def render_diagnostic(
    diag: Diagnostic,
    source: str | None = None,
    *,
    display_path: str | None = None,
    context_lines: int = 1,
    config: Config | None = None,
    color: bool = False,
    concise: bool = False,
) -> str:
    """Render a diagnostic.

    When *concise* is True (or *source* is not provided), returns a single-line
    header.  Otherwise renders in ruff-style format with source context.

    Example output (full)::

        example.py:9:8: PRM001 [*] Missing Args/Parameters section in docstring.
           |
         8 | def missing_args_section(x: int, y: str) -> None:
         9 |     \"\"\"Do something.\"\"\"
           |        ^^^^^^^^^^^^^^^ PRM001
        10 |     pass
           |

    Args:
        diag: The diagnostic to render.
        source: The full source code of the file. Required for full format.
        display_path: Path to display in the output. Defaults to diag.filepath.
        context_lines: Number of context lines to show around the violation.
        config: Configuration for computing effective fix applicability.
        color: Whether to apply ANSI color codes.
        concise: If True, render as a single-line header only.

    Returns:
        A formatted string.
    """
    path = display_path or diag.filepath
    start = diag.range.start
    tag = _fix_tag(diag, config, color=color)
    sep = _ansi(":", _DIM, color=color)
    rule_s = _ansi(diag.rule, _RED, _BOLD, color=color)
    header = f"{path}{sep}{start.lineno}{sep}{start.col}{sep} {rule_s} {tag} {diag.message}"

    if concise or source is None:
        return header

    # --- Source context ---
    start = diag.range.start
    end = diag.range.end
    source_lines = source.splitlines()
    n_lines = len(source_lines)

    if start.lineno < 1 or start.lineno > n_lines:
        return header

    first_ctx = max(1, start.lineno - context_lines)
    last_ctx = min(n_lines, end.lineno + context_lines)

    # Width for line number gutter (minimum 2 so arrows align nicely)
    gutter_width = max(len(str(last_ctx)), 2)

    def _gutter(lineno: int | None = None) -> str:
        raw = f"{lineno or '':>{gutter_width}} |"
        return _ansi(raw, _DIM, color=color)

    parts: list[str] = [header, _gutter()]

    # Track underline rows as (parts_index, raw_underline) to apply color and rule code after the loop
    underline_rows: list[tuple[int, str]] = []

    for lineno in range(first_ctx, last_ctx + 1):
        line_content = source_lines[lineno - 1].rstrip("\n\r")
        parts.append(f"{_gutter(lineno)} {line_content}")

        # Add underline row below each line that is part of the violation range
        if start.lineno <= lineno <= end.lineno:
            if lineno == start.lineno == end.lineno:
                # Single-line violation: underline exact range
                caret_start = start.col - 1  # convert 1-based col to 0-based
                caret_len = max(1, end.col - start.col)
            elif lineno == start.lineno:
                # First line of a multi-line violation
                caret_start = start.col - 1
                caret_len = max(1, len(line_content) - caret_start)
            elif lineno == end.lineno:
                # Last line of a multi-line violation
                caret_start = 0
                caret_len = max(1, end.col - 1)
            else:
                # Middle lines of a multi-line violation
                caret_start = 0
                caret_len = max(1, len(line_content))

            underline = " " * caret_start + "^" * caret_len
            parts.append(f"{_gutter()} {underline}")
            underline_rows.append((len(parts) - 1, underline))

    if underline_rows:
        gutter_str = _gutter()
        for idx, raw_underline in underline_rows:
            underline_s = _ansi(raw_underline, _RED, _BOLD, color=color)
            parts[idx] = f"{gutter_str} {underline_s}"

    parts.append(_gutter())
    return "\n".join(parts)
