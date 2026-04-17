"""Diagnostic rendering for pydocfix (ruff-style output)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydocfix.config import Config
    from pydocfix.rules._base import Diagnostic


def render_diagnostic(
    diag: Diagnostic,
    source: str,
    *,
    display_path: str | None = None,
    context_lines: int = 1,
    config: Config | None = None,
) -> str:
    """Render a diagnostic in ruff-style format.

    Example output::

        PRM001 [unsafe] Missing Args/Parameters section in docstring.
          --> example.py:9:8
           |
         8 | def missing_args_section(x: int, y: str) -> None:
         9 |     \"\"\"Do something.\"\"\"
           |        ^^^^^^^^^^^^^^^
        10 |     pass
           |

    Args:
        diag: The diagnostic to render.
        source: The full source code of the file.
        display_path: Path to display in the output. Defaults to diag.filepath.
        context_lines: Number of context lines to show around the violation.
        config: Configuration for computing effective fix applicability.

    Returns:
        A formatted string ready to print.
    """
    from pydocfix.rules._base import Applicability, effective_applicability

    path = display_path or diag.filepath
    start = diag.range.start
    end = diag.range.end

    # --- Header ---
    if diag.fix is not None:
        app = effective_applicability(diag, config)
        if app == Applicability.SAFE:
            fix_tag = " [*]"
        elif app == Applicability.UNSAFE:
            fix_tag = " [unsafe]"
        else:
            fix_tag = ""
    else:
        fix_tag = ""

    header = f"{path}:{start.lineno}:{start.col}: {diag.rule}{fix_tag} {diag.message}"

    # --- Source context ---
    source_lines = source.splitlines()
    n_lines = len(source_lines)

    if start.lineno < 1 or start.lineno > n_lines:
        return header

    first_ctx = max(1, start.lineno - context_lines)
    last_ctx = min(n_lines, end.lineno + context_lines)

    # Width for line number gutter (minimum 2 so arrows align nicely)
    gutter_width = max(len(str(last_ctx)), 2)

    def _gutter(lineno: int | None = None) -> str:
        if lineno is None:
            return " " * gutter_width + " |"
        return f"{lineno:>{gutter_width}} |"

    parts: list[str] = [header, _gutter()]

    last_underline_idx: int | None = None

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
            last_underline_idx = len(parts) - 1

    # Append rule code to the last underline row (Ruff style)
    if last_underline_idx is not None:
        parts[last_underline_idx] = parts[last_underline_idx] + f" {diag.rule}"

    parts.append(_gutter())
    return "\n".join(parts)
