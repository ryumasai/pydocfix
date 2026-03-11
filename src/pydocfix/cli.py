"""Command-line interface for pydocfix."""

from __future__ import annotations

import difflib
import logging
import sys
from pathlib import Path
from typing import Annotated, Final, Literal

import typer

logger = logging.getLogger(__name__)

app = typer.Typer(
    help="A Python docstring linter with auto-fix support.",
    no_args_is_help=True,
    add_completion=False,
)


def _version_callback(value: bool) -> None:
    if value:
        from pydocfix import __version__

        print(f"pydocfix {__version__}")
        raise typer.Exit


@app.callback()
def callback(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = None,
) -> None:
    """A Python docstring linter with auto-fix support."""


@app.command()
def check(
    paths: Annotated[
        list[str] | None,
        typer.Argument(help="Files or directories to check."),
    ] = None,
    fix: Annotated[
        bool,
        typer.Option("--fix", help="Automatically fix docstring issues."),
    ] = False,
    diff: Annotated[
        bool,
        typer.Option("--diff", help="Show diff of fixes without applying."),
    ] = False,
    unsafe_fixes: Annotated[
        bool,
        typer.Option("--unsafe-fixes", help="Also apply unsafe fixes."),
    ] = False,
) -> None:
    """Run linter on docstrings."""
    logging.basicConfig(format="pydocfix: %(levelname)s: %(message)s", level=logging.WARNING, stream=sys.stderr)

    from pydocfix.checker import build_kind_map, diagnose_file
    from pydocfix.fixer import fix_file
    from pydocfix.rules import build_registry

    registry = build_registry()
    rules = registry.all_rules()
    kind_map = build_kind_map(rules)

    targets = _collect_files(paths or ["."])
    if not targets:
        logger.warning("no Python files found.")
        raise typer.Exit(0)

    total_violations = 0
    total_fixed = 0

    for filepath in sorted(targets):
        diagnostics = diagnose_file(filepath, kind_map)
        if not diagnostics:
            continue

        total_violations += len(diagnostics)

        if fix or diff:
            applicable = _filter_applicable(diagnostics, unsafe_fixes)
            new_source = fix_file(filepath, applicable)
            if new_source is not None:
                if diff:
                    _print_diff(filepath, new_source)
                if fix:
                    filepath.write_text(new_source, encoding="utf-8")
                    fixed = sum(1 for d in applicable if d.fixable)
                    total_fixed += fixed
                    diagnostics = diagnose_file(filepath, kind_map)

        for d in diagnostics:
            hint = _fixable_hint(d, unsafe_fixes)
            print(f"{d.filepath}:{d.line}:{d.col}: {d.rule} {d.message}{hint}")

    remaining = total_violations - total_fixed

    if fix and total_fixed:
        print(f"\nFixed {total_fixed} violation(s).")

    if remaining > 0:
        raise typer.Exit(1)


def _filter_applicable(diagnostics: list, unsafe_fixes: bool) -> list:
    """Return diagnostics whose fixes should be applied."""
    from pydocfix.rules import Applicability

    result = []
    for d in diagnostics:
        if d.fix is None:
            continue
        if d.fix.applicability == Applicability.SAFE:
            result.append(d)
            continue
        if d.fix.applicability == Applicability.UNSAFE and unsafe_fixes:
            result.append(d)
            continue
    return result


def _fixable_hint(d, unsafe_fixes: bool) -> Literal["", " (fixable)", " (unsafe fix)"]:
    """Return a parenthetical hint about fixability."""
    from pydocfix.rules import Applicability

    unfixable: Final = ""
    fixable: Final = " (fixable)"
    unsafe: Final = " (unsafe fix)"

    if d.fix is None:
        return unfixable
    if d.fix.applicability == Applicability.SAFE:
        return fixable
    if d.fix.applicability == Applicability.UNSAFE:
        return unsafe if not unsafe_fixes else fixable
    return unfixable


def _print_diff(filepath: Path, new_source: str) -> None:
    """Print unified diff between original and fixed source."""
    original = filepath.read_text(encoding="utf-8")
    diff_lines = difflib.unified_diff(
        original.splitlines(keepends=True),
        new_source.splitlines(keepends=True),
        fromfile=str(filepath),
        tofile=str(filepath),
    )
    sys.stdout.writelines(diff_lines)


def _collect_files(paths: list[str]) -> list[Path]:
    """Resolve paths to a flat list of Python files."""

    suffixes: Final = {".py", ".pyi"}

    result: list[Path] = []
    for p in paths:
        path = Path(p)
        # TODO: exclude some dirs like __pycache__?
        if path.is_file() and path.suffix in suffixes:
            result.append(path)
        elif path.is_dir():
            for suffix in suffixes:
                result.extend(path.rglob(f"*{suffix}"))
        else:
            logger.warning("path not found or not a Python file: %s", p)
    return result


def main() -> None:
    app()


if __name__ == "__main__":
    sys.exit(main())
