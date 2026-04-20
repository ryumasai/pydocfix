"""Parallel file-checking infrastructure for pydocfix."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import NamedTuple

from pydocfix.config import Config
from pydocfix.engine.registry import RuleRegistry


class FileResult(NamedTuple):
    """Result of checking a single file."""

    filepath: Path
    source: str
    diagnostics: list
    new_source: str | None
    remaining: list


def check_one_file(
    filepath: Path,
    registry: RuleRegistry,
    fix: bool,
    unsafe_fixes: bool,
    config: Config | None,
    known_rule_codes: frozenset[str] | None = None,
) -> FileResult:
    """Read and check a single file. Used by both serial and parallel paths."""
    from pydocfix.engine.checker import check_file

    source = filepath.read_text(encoding="utf-8")
    diagnostics, new_source, remaining = check_file(
        source,
        filepath,
        registry,
        fix=fix,
        unsafe_fixes=unsafe_fixes,
        config=config,
        known_rule_codes=known_rule_codes,
    )
    return FileResult(filepath, source, diagnostics, new_source, remaining)


# --- multiprocessing worker ---

_worker_registry: RuleRegistry | None = None
_worker_known_rule_codes: frozenset[str] | None = None


def _worker_init(
    ignore: list[str] | None,
    select: list[str] | None,
    config_obj: Config | None,
    plugin_rule_classes: list[type] | None = None,
) -> None:
    """Initialize worker process by rebuilding the rule registry."""
    global _worker_registry, _worker_known_rule_codes  # noqa: PLW0603
    from pydocfix.rules import build_registry

    registry = build_registry(
        ignore=ignore,
        select=select,
        config=config_obj,
        plugin_rules=plugin_rule_classes,
    )
    _worker_registry = registry
    _worker_known_rule_codes = registry.all_codes()


def _worker_check(args: tuple) -> FileResult:
    """Worker function — runs in a child process."""
    filepath, fix, unsafe_fixes, config_obj = args

    if _worker_registry is None or _worker_known_rule_codes is None:
        raise RuntimeError("Worker process not initialized: _worker_init() must be called before _worker_check()")
    return check_one_file(filepath, _worker_registry, fix, unsafe_fixes, config_obj, _worker_known_rule_codes)


def check_files_parallel(
    targets: list[Path],
    num_workers: int,
    ignore: list[str] | None,
    select: list[str] | None,
    config: Config | None,
    *,
    fix: bool,
    unsafe_fixes: bool,
    plugin_rule_classes: list[type] | None = None,
) -> list[FileResult]:
    """Check files using multiple processes."""
    tasks = [(fp, fix, unsafe_fixes, config) for fp in targets]
    with ProcessPoolExecutor(
        max_workers=num_workers,
        initializer=_worker_init,
        initargs=(ignore, select, config, plugin_rule_classes),
    ) as pool:
        return list(pool.map(_worker_check, tasks))
