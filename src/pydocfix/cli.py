"""Command-line interface for pydocfix."""

from __future__ import annotations

import difflib
import logging
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Final, NamedTuple

import click

from pydocfix import __version__
from pydocfix.config import Config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Parallel file checking
# ---------------------------------------------------------------------------


class _FileResult(NamedTuple):
    """Result of checking a single file."""

    filepath: Path
    source: str
    diagnostics: list
    new_source: str | None
    remaining: list


def _check_one_file(
    filepath: Path,
    type_to_rules: dict,
    fix: bool,
    unsafe_fixes: bool,
    config: Config | None,
    known_rule_codes: frozenset[str] | None = None,
) -> _FileResult:
    """Read and check a single file. Used by both serial and parallel paths."""
    from pydocfix.checker import check_file

    source = filepath.read_text(encoding="utf-8")
    diagnostics, new_source, remaining = check_file(
        source,
        filepath,
        type_to_rules,
        fix=fix,
        unsafe_fixes=unsafe_fixes,
        config=config,
        known_rule_codes=known_rule_codes,
    )
    return _FileResult(filepath, source, diagnostics, new_source, remaining)


# --- multiprocessing worker ---

_worker_type_to_rules: dict | None = None
_worker_known_rule_codes: frozenset[str] | None = None


def _worker_init(
    ignore: list[str] | None,
    select: list[str] | None,
    config_obj: Config | None,
    plugin_rule_classes: list[type] | None = None,
) -> None:
    """Initialize worker process by rebuilding the rule registry."""
    global _worker_type_to_rules, _worker_known_rule_codes  # noqa: PLW0603
    from pydocfix.rules import build_registry

    registry = build_registry(
        ignore=ignore,
        select=select,
        config=config_obj,
        plugin_rules=plugin_rule_classes,
    )
    _worker_type_to_rules = registry.type_to_rules
    _worker_known_rule_codes = registry.all_codes()


def _worker_check(args: tuple) -> _FileResult:
    """Worker function — runs in a child process."""
    filepath, fix, unsafe_fixes, config_obj = args

    assert _worker_type_to_rules is not None
    assert _worker_known_rule_codes is not None
    return _check_one_file(filepath, _worker_type_to_rules, fix, unsafe_fixes, config_obj, _worker_known_rule_codes)


def _check_files_parallel(
    targets: list[Path],
    num_workers: int,
    ignore: list[str] | None,
    select: list[str] | None,
    config: Config | None,
    *,
    fix: bool,
    unsafe_fixes: bool,
    plugin_rule_classes: list[type] | None = None,
) -> list[_FileResult]:
    """Check files using multiple processes."""
    tasks = [(fp, fix, unsafe_fixes, config) for fp in targets]
    with ProcessPoolExecutor(
        max_workers=num_workers,
        initializer=_worker_init,
        initargs=(ignore, select, config, plugin_rule_classes),
    ) as pool:
        return list(pool.map(_worker_check, tasks))


@click.group()
@click.version_option(__version__, "--version", message="pydocfix %(version)s")
def cli() -> None:
    """Lint and auto-fix Python docstrings."""


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
@click.option(
    "--exclude",
    "exclude_dirs",
    multiple=True,
    metavar="DIRS",
    help="Comma-separated directory names to exclude (e.g. build,dist). Added to default exclusions.",
)
@click.option(
    "--baseline",
    "baseline_path",
    default=None,
    metavar="FILE",
    help="Path to baseline JSON file. Violations in the baseline are suppressed.",
)
@click.option(
    "--generate-baseline",
    is_flag=True,
    help="Generate (or overwrite) the baseline file with all current violations.",
)
@click.option(
    "--jobs",
    default=None,
    type=int,
    metavar="N",
    help="Number of parallel workers.  Defaults to CPU count for >=8 files, else 1.",
)
def check(
    paths: tuple[str, ...],
    fix: bool,
    diff: bool,
    unsafe_fixes: bool,
    select_codes: tuple[str, ...],
    ignore_codes: tuple[str, ...],
    exclude_dirs: tuple[str, ...],
    baseline_path: str | None,
    generate_baseline: bool,
    jobs: int | None,
) -> None:
    """Run linter on docstrings."""
    logging.basicConfig(format="pydocfix: %(levelname)s: %(message)s", level=logging.WARNING, stream=sys.stderr)

    from pydocfix.baseline import (
        compute_updated_baseline,
        filter_baseline_violations,
        load_baseline,
        normalize_path,
    )
    from pydocfix.baseline import (
        generate_baseline as _generate_baseline,
    )
    from pydocfix.baseline import (
        write_baseline as _write_baseline,
    )
    from pydocfix.config import DEFAULT_EXCLUDE, find_pyproject_toml, load_config
    from pydocfix.rules import Applicability, build_registry, effective_applicability, load_plugin_rules

    config = load_config()

    # Load plugin rules from config
    plugin_rule_classes: list[type] = []
    if config.plugin_modules or config.plugin_paths:
        plugin_paths_objs = [Path(p) for p in config.plugin_paths]
        try:
            plugin_rule_classes = load_plugin_rules(
                plugin_modules=config.plugin_modules or None,
                plugin_paths=plugin_paths_objs or None,
            )
            if plugin_rule_classes:
                logger.info(f"Loaded {len(plugin_rule_classes)} plugin rule(s)")
        except Exception as e:
            logger.error(f"Failed to load plugins: {e}")

    # Determine project root for stable relative-path keys in baseline files
    _toml = find_pyproject_toml()
    project_root: Path = _toml.parent if _toml is not None else Path.cwd()

    # Resolve baseline path: CLI > config > None
    effective_baseline_path: Path | None = None
    if baseline_path:
        effective_baseline_path = Path(baseline_path)
    elif config.baseline:
        effective_baseline_path = Path(config.baseline)

    # Load existing baseline (empty dict if none)
    baseline_data = (
        load_baseline(effective_baseline_path) if (effective_baseline_path and not generate_baseline) else {}
    )

    # CLI --select / --ignore override config file values when provided
    def _parse_codes(raw: tuple[str, ...]) -> list[str]:
        return [code.strip() for group in raw for code in group.split(",") if code.strip()]

    effective_select = _parse_codes(select_codes) if select_codes else config.select
    effective_ignore = _parse_codes(ignore_codes) if ignore_codes else config.ignore

    # Build effective exclude set: defaults + config + CLI
    cli_excludes = [d.strip() for group in exclude_dirs for d in group.split(",") if d.strip()]
    effective_exclude: frozenset[str] = DEFAULT_EXCLUDE | frozenset(config.exclude) | frozenset(cli_excludes)

    registry: Final = build_registry(
        ignore=effective_ignore,
        select=effective_select,
        config=config,
        plugin_rules=plugin_rule_classes or None,
    )
    type_to_rules: Final = registry.type_to_rules
    known_rule_codes: Final = registry.all_codes()

    targets: Final = _collect_files(list(paths) or ["."], exclude=effective_exclude)
    if not targets:
        logger.warning("no Python files found.")
        sys.exit(0)

    # Decide parallelism: explicit -j, or auto (CPU count for >=8 files)
    num_workers = jobs if jobs is not None else (os.cpu_count() or 1 if len(targets) >= 8 else 1)
    num_workers = max(1, min(num_workers, len(targets)))

    total_violations = 0
    total_fixed = 0
    total_would_fix = 0
    total_safe_fixable = 0
    total_unsafe_fixable = 0
    remaining_diagnostics: list = []
    # Collect raw (pre-baseline-filter) violations for baseline generation / auto-regen
    raw_violations_by_file: dict[str, list] = {}

    # --- Check files (parallel or sequential) ---
    do_fix = fix or diff
    file_results: list[_FileResult]
    if num_workers > 1:
        file_results = _check_files_parallel(
            sorted(targets),
            num_workers,
            effective_ignore,
            effective_select,
            config,
            fix=do_fix,
            unsafe_fixes=unsafe_fixes,
            plugin_rule_classes=plugin_rule_classes or None,
        )
    else:
        file_results = [
            _check_one_file(fp, type_to_rules, do_fix, unsafe_fixes, config, known_rule_codes) for fp in sorted(targets)
        ]

    for result in file_results:
        filepath = result.filepath
        source = result.source
        diagnostics = result.diagnostics
        new_source = result.new_source
        remaining = result.remaining

        fp_str = normalize_path(filepath, project_root)
        if diagnostics:
            raw_violations_by_file[fp_str] = list(diagnostics)

        # When generating the baseline, skip filtering and reporting
        if generate_baseline:
            continue

        # Apply baseline filtering to both first-pass and remaining diagnostics
        if baseline_data:
            diagnostics = filter_baseline_violations(diagnostics, baseline_data, fp_str)
            remaining = filter_baseline_violations(remaining, baseline_data, fp_str)

        if not diagnostics:
            continue

        total_violations += len(diagnostics)

        for d in diagnostics:
            if d.fix is not None:
                app = effective_applicability(d, config)
                if app == Applicability.SAFE:
                    total_safe_fixable += 1
                elif app == Applicability.UNSAFE:
                    total_unsafe_fixable += 1

        if new_source is not None:
            if diff:
                _print_diff(filepath, source, new_source)
                total_would_fix += len(diagnostics) - len(remaining)
            if fix:
                filepath.write_text(new_source, encoding="utf-8")
                total_fixed += len(diagnostics) - len(remaining)
                diagnostics = remaining

        from pydocfix.render import render_diagnostic

        for d in diagnostics:
            display_path = normalize_path(Path(d.filepath), project_root)
            click.echo(render_diagnostic(d, source, display_path=display_path, config=config))
            click.echo()

        remaining_diagnostics.extend(diagnostics)

    # --- Baseline generation ---
    if generate_baseline:
        if effective_baseline_path is None:
            click.echo(
                click.style("Error: ", fg="red")
                + "specify a baseline path with --baseline or [tool.pydocfix] baseline in pyproject.toml.",
                err=True,
            )
            sys.exit(2)
        _generate_baseline(raw_violations_by_file, effective_baseline_path)
        total_raw = sum(len(v) for v in raw_violations_by_file.values())
        click.echo(
            click.style("Baseline generated: ", fg="green")
            + f"{effective_baseline_path} ({total_raw} violation(s) across {len(raw_violations_by_file)} file(s))"
        )
        sys.exit(0)

    # --- Auto-regenerate baseline when violations have been fixed ---
    if effective_baseline_path and baseline_data:
        changed, updated = compute_updated_baseline(baseline_data, raw_violations_by_file)
        if changed:
            _write_baseline(updated, effective_baseline_path)
            logger.info("baseline auto-updated: %s", effective_baseline_path)

    remaining = total_violations - total_fixed

    if total_violations == 0:
        click.echo(click.style("All checks passed.", fg="green") + f" ({len(targets)} file(s) checked)")
    elif fix:
        _summarize_fix(total_fixed, remaining, remaining_diagnostics, unsafe_fixes, config)
    elif diff:
        _summarize_diff(total_violations, total_would_fix, total_unsafe_fixable, unsafe_fixes)
    else:
        _summarize_check(total_violations, total_safe_fixable, total_unsafe_fixable)

    if remaining > 0:
        sys.exit(1)


def _summarize_check(total: int, safe: int, unsafe: int) -> None:
    """Print summary for check mode (no --fix)."""
    if safe and unsafe:
        click.echo(
            f"Found {total} violation(s). "
            f"Run --fix to auto-fix {safe} of them "
            f"({unsafe} more with --fix --unsafe-fixes)."
        )
    elif safe:
        click.echo(f"Found {total} violation(s). Run --fix to auto-fix {safe} of them.")
    elif unsafe:
        click.echo(f"Found {total} violation(s). Run --fix --unsafe-fixes to fix {unsafe} of them.")
    else:
        click.echo(f"Found {total} violation(s). No auto-fixes available.")


def _summarize_fix(
    total_fixed: int, remaining: int, remaining_diagnostics: list, unsafe_fixes: bool, config=None
) -> None:
    """Print summary for --fix mode."""
    from pydocfix.rules import Applicability, effective_applicability

    if total_fixed and not remaining:
        click.echo(click.style(f"Fixed {total_fixed} violation(s). No issues remaining.", fg="green"))
    elif total_fixed and remaining:
        remaining_unsafe = sum(
            1
            for d in remaining_diagnostics
            if d.fix is not None and effective_applicability(d, config) == Applicability.UNSAFE
        )
        msg = f"Fixed {total_fixed} violation(s). {remaining} remaining"
        if remaining_unsafe and not unsafe_fixes:
            msg += f" ({remaining_unsafe} fixable with --unsafe-fixes)"
        msg += "."
        click.echo(msg)
    else:
        remaining_unsafe = sum(
            1
            for d in remaining_diagnostics
            if d.fix is not None and effective_applicability(d, config) == Applicability.UNSAFE
        )
        if remaining_unsafe and not unsafe_fixes:
            click.echo(f"Found {remaining} violation(s). Run --fix --unsafe-fixes to fix {remaining_unsafe} of them.")
        else:
            click.echo(f"Found {remaining} violation(s). No auto-fixes available.")


def _summarize_diff(total: int, would_fix: int, unsafe_fixable: int, unsafe_fixes: bool) -> None:
    """Print summary for --diff mode."""
    remaining = total - would_fix
    if would_fix:
        msg = f"Would fix {would_fix} violation(s)."
        if remaining > 0:
            if unsafe_fixable and not unsafe_fixes:
                msg += f" {remaining} remaining ({unsafe_fixable} fixable with --diff --unsafe-fixes)."
            else:
                msg += f" {remaining} remaining."
        click.echo(msg)
    else:
        if unsafe_fixable and not unsafe_fixes:
            click.echo(f"Found {total} violation(s). Run --diff --unsafe-fixes to fix {unsafe_fixable} of them.")
        else:
            click.echo(f"Found {total} violation(s). No auto-fixes available.")


def _print_diff(filepath: Path, original: str, new_source: str) -> None:
    """Print unified diff between original and fixed source."""
    diff_lines = difflib.unified_diff(
        original.splitlines(keepends=True),
        new_source.splitlines(keepends=True),
        fromfile=str(filepath),
        tofile=str(filepath),
    )
    sys.stdout.writelines(diff_lines)


def _collect_files(
    paths: list[str],
    exclude: frozenset[str] = frozenset(),
) -> list[Path]:
    """Resolve paths to a flat list of Python files, skipping excluded directories."""
    suffixes: Final = {".py", ".pyi"}

    def _walk(directory: Path) -> list[Path]:
        found: list[Path] = []
        for entry in directory.iterdir():
            if entry.is_dir():
                if entry.name not in exclude:
                    found.extend(_walk(entry))
            elif entry.is_file() and entry.suffix in suffixes:
                found.append(entry)
        return found

    result: list[Path] = []
    for p in paths:
        path = Path(p)
        if path.is_file() and path.suffix in suffixes:
            result.append(path)
        elif path.is_dir():
            result.extend(_walk(path))
        else:
            logger.warning("path not found or not a Python file: %s", p)
    return result


def main() -> None:
    """Entry point for console script. Calls the CLI group function."""
    cli()


if __name__ == "__main__":
    sys.exit(main())
