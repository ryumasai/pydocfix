"""Shared test fixtures and utilities for rule tests."""

from __future__ import annotations

import difflib
from collections.abc import Sequence
from pathlib import Path

from pydocfix.checker import check_file
from pydocfix.rules import BaseRule


def load_fixture(fixture_name: str, category: str) -> Path:
    """Load a fixture file by name.

    Args:
        fixture_name: Relative path to the fixture file within the fixtures dir
            (e.g., "prm001.py" or "prm001/violation_basic.py").
        category: Rule category (e.g., "prm", "rtn", "sum").

    Returns:
        Path to the fixture file.

    Example:
        >>> path = load_fixture("prm001.py", "prm")
        >>> output = render_fixture(path, [PRM001(Config())])
    """
    fixture_dir = Path(__file__).parent / category / "fixtures"
    fixture_path = fixture_dir / fixture_name
    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture not found: {fixture_path}")
    return fixture_path


def render_fixture(
    fixture_path: Path,
    rules: Sequence[BaseRule],
    *,
    display_path: str | None = None,
) -> str:
    """Run rules on fixture and return rendered diagnostic string.

    Args:
        fixture_path: Path to the fixture file.
        rules: List of rule instances to apply.
        display_path: Path to display in diagnostics (defaults to fixture filename).

    Returns:
        Rendered diagnostic string (ruff-style), deduplicated by (rule, lineno, col).
    """
    from pydocfix.checker import build_rules_map
    from pydocfix.render import render_diagnostic

    source = fixture_path.read_text(encoding="utf-8")
    type_to_rules = build_rules_map(rules)
    diagnostics, _, _ = check_file(source, fixture_path, type_to_rules)

    seen: set[tuple[str, int, int]] = set()
    unique_diags = []
    for d in diagnostics:
        key = (d.rule, d.range.start.lineno, d.range.start.col)
        if key not in seen:
            seen.add(key)
            unique_diags.append(d)

    path_str = display_path or fixture_path.name
    if not unique_diags:
        return "(none)"
    return "\n\n".join(render_diagnostic(d, source, display_path=path_str, context_lines=2) for d in unique_diags)


def fix_fixture(
    fixture_path: Path,
    rules: Sequence[BaseRule],
    *,
    unsafe_fixes: bool = True,
) -> str | None:
    """Run rules on fixture with fix=True and return fixed source.

    Args:
        fixture_path: Path to the fixture file.
        rules: List of rule instances to apply.
        unsafe_fixes: Whether to apply unsafe fixes (default True).

    Returns:
        Fixed source string, or None if no fix was applied.
    """
    from pydocfix.checker import build_rules_map

    source = fixture_path.read_text(encoding="utf-8")
    type_to_rules = build_rules_map(rules)
    _, fixed_source, _ = check_file(
        source,
        fixture_path,
        type_to_rules,
        fix=True,
        unsafe_fixes=unsafe_fixes,
    )
    return fixed_source


def _section_sep(label: str, width: int = 50) -> str:
    """Return a section separator like '━━━ Diagnostics ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'."""
    prefix = f"━━━ {label} "
    return prefix + "━" * max(0, width - len(prefix))


def check_rule(
    fixture_path: Path,
    rules: Sequence[BaseRule],
    *,
    display_path: str | None = None,
    unsafe_fixes: bool = True,
) -> str:
    """Run rules on fixture and return combined diagnostics + diff snapshot.

    The output format is::

        ━━━ Diagnostics ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        RTN001 [unsafe] Missing Returns section in docstring.
          --> rtn001.py:7:8
           |
         6 | def missing_returns_section(x: int) -> int:
         7 |     \"\"\"Do something.\"\"\"
           |        ^^^^^^^^^^^^^
         8 |     return x
           |

        ━━━ Diff ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        --- rtn001.py
        +++ rtn001.py (fixed)
        @@ ... @@
        ...

    If there are no diagnostics, the Diagnostics section shows ``(none)``.
    If there is no fix, the Diff section shows ``(no fix)``.

    Args:
        fixture_path: Path to the fixture file.
        rules: List of rule instances to apply.
        display_path: Path to display in diagnostics (defaults to fixture filename).
        unsafe_fixes: Whether to apply unsafe fixes (default True).

    Returns:
        Combined string with diagnostics and diff sections.
    """
    path_str = display_path or fixture_path.name
    source = fixture_path.read_text(encoding="utf-8")

    diag_output = render_fixture(fixture_path, rules, display_path=path_str)
    fixed = fix_fixture(fixture_path, rules, unsafe_fixes=unsafe_fixes)

    diag_sep = _section_sep("Diagnostics")
    diff_sep = _section_sep("Diff")

    diag_section = f"{diag_sep}\n\n{diag_output}"

    if fixed is None:
        diff_content = "(no fix)"
    else:
        diff_lines = list(
            difflib.unified_diff(
                source.splitlines(keepends=True),
                fixed.splitlines(keepends=True),
                fromfile=path_str,
                tofile=f"{path_str} (fixed)",
            )
        )
        diff_content = "".join(diff_lines).rstrip()

    diff_section = f"{diff_sep}\n\n{diff_content}"
    return f"{diag_section}\n\n{diff_section}"
