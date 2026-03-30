"""Command-line interface for pydocfix."""

from __future__ import annotations

import difflib
import logging
import sys
from pathlib import Path
from typing import Final, Literal

import click

from pydocfix import __version__

logger = logging.getLogger(__name__)


@click.group()
@click.version_option(__version__, "--version", message="pydocfix %(version)s")
def cli() -> None:
    """A Python docstring linter with auto-fix support."""


@cli.command()
@click.argument("paths", nargs=-1)
@click.option("--fix", is_flag=True, help="Automatically fix docstring issues.")
@click.option("--diff", is_flag=True, help="Show diff of fixes without applying.")
@click.option("--unsafe-fixes", is_flag=True, help="Also apply unsafe fixes.")
@click.option(
    "--select",
    "select_codes",
    multiple=True,
    metavar="CODES",
    help="Comma-separated rule codes to enable (e.g. PRM001,RTN101). Overrides config. Use ALL to enable every rule.",
)
@click.option(
    "--ignore",
    "ignore_codes",
    multiple=True,
    metavar="CODES",
    help="Comma-separated rule codes to ignore (e.g. SUM001,PRM002). Overrides config.",
)
def check(
    paths: tuple[str, ...],
    fix: bool,
    diff: bool,
    unsafe_fixes: bool,
    select_codes: tuple[str, ...],
    ignore_codes: tuple[str, ...],
) -> None:
    """Run linter on docstrings."""
    logging.basicConfig(format="pydocfix: %(levelname)s: %(message)s", level=logging.WARNING, stream=sys.stderr)

    from pydocfix.checker import check_file
    from pydocfix.config import load_config
    from pydocfix.rules import build_registry

    config = load_config()

    # CLI --select / --ignore override config file values when provided
    def _parse_codes(raw: tuple[str, ...]) -> list[str]:
        return [code.strip() for group in raw for code in group.split(",") if code.strip()]

    effective_select = _parse_codes(select_codes) if select_codes else config.select
    effective_ignore = _parse_codes(ignore_codes) if ignore_codes else config.ignore

    registry: Final = build_registry(ignore=effective_ignore, select=effective_select, config=config)
    kind_map: Final = registry.kind_map

    targets: Final = _collect_files(list(paths) or ["."])
    if not targets:
        logger.warning("no Python files found.")
        sys.exit(0)

    total_violations = 0
    total_fixed = 0

    for filepath in sorted(targets):
        source = filepath.read_text(encoding="utf-8")
        diagnostics, new_source, fixed_indices = check_file(
            source, filepath, kind_map, fix=(fix or diff), unsafe_fixes=unsafe_fixes, config=config
        )
        if not diagnostics:
            continue

        total_violations += len(diagnostics)

        if new_source is not None:
            if diff:
                _print_diff(filepath, source, new_source)
            if fix:
                filepath.write_text(new_source, encoding="utf-8")
                total_fixed += len(fixed_indices)
                diagnostics = [d for i, d in enumerate(diagnostics) if i not in fixed_indices]

        for d in diagnostics:
            hint = _fixable_hint(d, unsafe_fixes)
            print(f"{d.filepath}:{d.lineno}:{d.col}: {d.rule} {d.message}{hint}")

    remaining = total_violations - total_fixed

    if fix and total_fixed:
        print(f"\nFixed {total_fixed} violation(s).")

    if remaining > 0:
        sys.exit(1)


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


def _print_diff(filepath: Path, original: str, new_source: str) -> None:
    """Print unified diff between original and fixed source."""
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
    cli()


if __name__ == "__main__":
    sys.exit(main())
