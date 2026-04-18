"""Command-line interface for pydocfix."""

from __future__ import annotations

import difflib
import logging
import os
import sys
from pathlib import Path
from typing import Final

import click

from pydocfix import __version__
from pydocfix._filewalker import collect_files
from pydocfix._parallel import FileResult, check_files_parallel, check_one_file

logger = logging.getLogger(__name__)


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
@click.option(
    "--output-format",
    "output_format",
    default=None,
    type=click.Choice(["full", "concise"], case_sensitive=False),
    help="Diagnostic output format: 'full' (default, with source context) or 'concise' (single-line).",
)
@click.option(
    "--no-color",
    "no_color",
    is_flag=True,
    help="Disable color output.",
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
    output_format: str | None,
    no_color: bool,
) -> None:
    """Run linter on docstrings."""
    logging.basicConfig(format="pydocfix: %(levelname)s: %(message)s", level=logging.WARNING, stream=sys.stderr)

    use_color = _should_use_color(no_color)

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
                logger.info("Loaded %d plugin rule(s)", len(plugin_rule_classes))
        except Exception as e:
            logger.error("Failed to load plugins: %s", e)

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

    targets: Final = collect_files(list(paths) or ["."], exclude=effective_exclude, root=project_root)
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
    # Pre-build baseline lookup once so it is not rebuilt per-file in the loop
    from pydocfix.baseline import _build_lookup as _build_baseline_lookup

    baseline_lookup = _build_baseline_lookup(baseline_data) if baseline_data else {}

    # --- Check files (parallel or sequential) ---
    do_fix = fix or diff
    file_results: list[FileResult]
    if num_workers > 1:
        file_results = check_files_parallel(
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
            check_one_file(fp, type_to_rules, do_fix, unsafe_fixes, config, known_rule_codes) for fp in sorted(targets)
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
            diagnostics = filter_baseline_violations(
                diagnostics,
                baseline_data,
                fp_str,
                prebuilt_lookup=baseline_lookup,
            )
            remaining = filter_baseline_violations(
                remaining,
                baseline_data,
                fp_str,
                prebuilt_lookup=baseline_lookup,
            )

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
                _print_diff(filepath, source, new_source, color=use_color)
                total_would_fix += len(diagnostics) - len(remaining)
            if fix:
                filepath.write_text(new_source, encoding="utf-8")
                total_fixed += len(diagnostics) - len(remaining)
                diagnostics = remaining

        if not diff:
            from pydocfix._render import render_diagnostic

            effective_format = output_format or config.output_format
            is_concise = effective_format == "concise"
            for d in diagnostics:
                display_path = normalize_path(Path(d.filepath), project_root)
                click.echo(
                    render_diagnostic(
                        d, source, display_path=display_path, config=config, color=use_color, concise=is_concise
                    ),
                    color=use_color or None,
                )
                if not is_concise:
                    click.echo()

        remaining_diagnostics.extend(diagnostics)

    # --- Baseline generation ---
    from pydocfix._ansi import _BOLD, _GREEN, _RED
    from pydocfix._ansi import ansi as _ansi

    if generate_baseline:
        if effective_baseline_path is None:
            click.echo(
                _ansi("Error: ", _RED, _BOLD, color=use_color)
                + "specify a baseline path with --baseline or [tool.pydocfix] baseline in pyproject.toml.",
                err=True,
                color=use_color or None,
            )
            sys.exit(2)
        _generate_baseline(raw_violations_by_file, effective_baseline_path)
        total_raw = sum(len(v) for v in raw_violations_by_file.values())
        click.echo(
            _ansi("Baseline generated: ", _GREEN, _BOLD, color=use_color)
            + f"{effective_baseline_path} ({total_raw} violation(s) across {len(raw_violations_by_file)} file(s))",
            color=use_color or None,
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
        click.echo(
            _ansi("All checks passed.", _GREEN, _BOLD, color=use_color) + f" ({len(targets)} file(s) checked)",
            color=True if use_color else None,
        )
    elif fix:
        _summarize_fix(total_fixed, remaining, remaining_diagnostics, unsafe_fixes, config, color=use_color)
    elif diff:
        _summarize_check(
            total_violations,
            total_safe_fixable,
            total_unsafe_fixable,
            diff=True,
            unsafe_fixes=unsafe_fixes,
            color=use_color,
        )
    else:
        _summarize_check(total_violations, total_safe_fixable, total_unsafe_fixable, color=use_color)

    if remaining > 0:
        sys.exit(1)


def _should_use_color(no_color_flag: bool) -> bool:
    """Return True if ANSI color output should be used."""
    if no_color_flag:
        return False
    if "NO_COLOR" in os.environ:
        return False
    if "FORCE_COLOR" in os.environ:
        return True
    return sys.stdout.isatty()


def _summarize_check(
    total: int,
    safe: int,
    unsafe: int,
    *,
    diff: bool = False,
    unsafe_fixes: bool = False,
    color: bool = False,
) -> None:
    """Print summary for check and diff modes."""
    from pydocfix._ansi import _BOLD, _RED
    from pydocfix._ansi import ansi as _ansi

    found_s = _ansi(f"Found {total} violation(s).", _RED, _BOLD, color=color)
    safe_s = _ansi(str(safe), _BOLD, color=color)
    unsafe_s = _ansi(str(unsafe), _BOLD, color=color)

    def _echo(msg: str) -> None:
        click.echo(msg, color=color or None)
    if diff:
        if safe and unsafe:
            if not unsafe_fixes:
                _echo(f"{found_s} Run --diff --unsafe-fixes to also show {unsafe_s} unsafe fix(es).")
            else:
                _echo(f"{found_s} Run --fix --unsafe-fixes to apply all fixes.")
        elif safe:
            if not unsafe_fixes:
                _echo(f"{found_s} Run --fix to apply {safe_s} fix(es).")
            else:
                _echo(f"{found_s} Run --fix --unsafe-fixes to apply all fixes.")
        elif unsafe:
            if not unsafe_fixes:
                _echo(f"{found_s} Run --diff --unsafe-fixes to show the diff.")
            else:
                _echo(f"{found_s} Run --fix --unsafe-fixes to apply the fix.")
        else:
            _echo(f"{found_s} No auto-fixes available.")
    else:
        if safe and unsafe:
            _echo(f"{found_s} Run --fix to auto-fix {safe_s} of them ({unsafe_s} more with --fix --unsafe-fixes).")
        elif safe:
            _echo(f"{found_s} Run --fix to auto-fix {safe_s} of them.")
        elif unsafe:
            _echo(f"{found_s} Run --fix --unsafe-fixes to fix {unsafe_s} of them.")
        else:
            _echo(f"{found_s} No auto-fixes available.")


def _summarize_fix(
    total_fixed: int,
    remaining: int,
    remaining_diagnostics: list,
    unsafe_fixes: bool,
    config=None,
    *,
    color: bool = False,
) -> None:
    """Print summary for --fix mode."""
    from pydocfix._ansi import _BOLD, _GREEN, _RED
    from pydocfix._ansi import ansi as _ansi
    from pydocfix.rules import Applicability, effective_applicability

    def _echo(msg: str) -> None:
        click.echo(msg, color=color or None)

    if total_fixed and not remaining:
        _echo(_ansi(f"Fixed {total_fixed} violation(s). No issues remaining.", _GREEN, color=color))
    elif total_fixed and remaining:
        remaining_unsafe = sum(
            1
            for d in remaining_diagnostics
            if d.fix is not None and effective_applicability(d, config) == Applicability.UNSAFE
        )
        remaining_s = _ansi(str(remaining), _BOLD, color=color)
        remaining_unsafe_s = _ansi(str(remaining_unsafe), _BOLD, color=color)
        msg = f"Fixed {total_fixed} violation(s). {remaining_s} remaining"
        if remaining_unsafe and not unsafe_fixes:
            msg += f" ({remaining_unsafe_s} fixable with --unsafe-fixes)"
        msg += "."
        _echo(msg)
    else:
        remaining_unsafe = sum(
            1
            for d in remaining_diagnostics
            if d.fix is not None and effective_applicability(d, config) == Applicability.UNSAFE
        )
        found_s = _ansi(f"Found {remaining} violation(s).", _RED, _BOLD, color=color)
        remaining_unsafe_s = _ansi(str(remaining_unsafe), _BOLD, color=color)
        if remaining_unsafe and not unsafe_fixes:
            _echo(f"{found_s} Run --fix --unsafe-fixes to fix {remaining_unsafe_s} of them.")
        else:
            _echo(f"{found_s} No auto-fixes available.")


def _print_diff(filepath: Path, original: str, new_source: str, *, color: bool = False) -> None:
    """Print unified diff between original and fixed source."""
    from pydocfix._ansi import _BOLD, _DIM, _GREEN, _RED
    from pydocfix._ansi import ansi as _ansi

    diff_lines = difflib.unified_diff(
        original.splitlines(keepends=True),
        new_source.splitlines(keepends=True),
        fromfile=str(filepath),
        tofile=str(filepath),
    )

    _prefix_codes = [
        ("+++", (_GREEN, _BOLD)),
        ("---", (_RED, _BOLD)),
        ("+", (_GREEN,)),
        ("-", (_RED,)),
        ("@@", (_DIM,)),
    ]
    for line in diff_lines:
        code = next((c for p, c in _prefix_codes if line.startswith(p)), None)
        if code is not None:
            click.echo(_ansi(line, *code, color=color), nl=False, color=True if color else None)
        else:
            sys.stdout.write(line)
    click.echo()


def main() -> None:
    """Entry point for console script. Calls the CLI group function."""
    cli()


if __name__ == "__main__":
    sys.exit(main())
