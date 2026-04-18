"""Baseline support for pydocfix.

Baseline allows recording the current violation state of a project so that
only *new* violations are reported on subsequent runs.  This makes gradual
adoption easier: fix violations at your own pace instead of all at once.

File format (JSON):

    {
      "src/module.py": [
        {"symbol": "MyClass.my_method", "code": "PRM001"},
        {"symbol": "other_func", "code": "RTN101"}
      ]
    }

Keys are file paths as strings (typically relative to the project root).
Each entry identifies a violation by the qualified symbol name and rule code.
Line numbers are intentionally omitted so that the baseline remains stable
when unrelated code is added or removed.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydocfix.rules import Diagnostic

logger = logging.getLogger(__name__)

# A baseline entry: the set of (symbol, code) pairs per file.
# Represented as a dict[filepath_str, list[dict]] for JSON serialisation.
BaselineData = dict[str, list[dict[str, str]]]


# ---------------------------------------------------------------------------
# Path normalisation
# ---------------------------------------------------------------------------


def normalize_path(filepath: Path, root: Path) -> str:
    """Return a POSIX path string for *filepath* relative to *root*.

    Paths are resolved before the comparison so that symbolic links and
    ``..`` components do not cause spurious mismatches.  Falls back to the
    absolute path string when *filepath* is not located under *root* (e.g.
    when linting files outside the project tree).
    """
    try:
        return filepath.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(filepath.resolve())


# ---------------------------------------------------------------------------
# Read / write
# ---------------------------------------------------------------------------


def load_baseline(path: Path) -> BaselineData:
    """Load a baseline JSON file and return the parsed data.

    Returns an empty dict if the file does not exist.
    """
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as exc:
        logger.warning("could not read baseline file %s: %s", path, exc)
        return {}
    if not isinstance(data, dict):
        logger.warning("baseline file %s has unexpected format", path)
        return {}
    return data


def write_baseline(data: BaselineData, path: Path) -> None:
    """Write pre-built baseline data to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as fh:
            tmp_path = Path(fh.name)
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        tmp_path.replace(path)
    finally:
        if tmp_path is not None and tmp_path.exists():
            tmp_path.unlink()
    logger.info("baseline written to %s (%d file(s))", path, len(data))


def generate_baseline(
    violations_by_file: dict[str, list[Diagnostic]],
    path: Path,
) -> None:
    """Write a baseline JSON file from the current set of violations.

    *violations_by_file* maps file path strings to lists of Diagnostic objects.
    Only violations that have a non-empty symbol are recorded.
    """
    data: BaselineData = {}
    for filepath, diagnostics in sorted(violations_by_file.items()):
        entries = [
            {"symbol": d.symbol, "code": d.rule}
            for d in diagnostics
            if d.symbol  # skip diagnostics without a symbol (module-level)
        ]
        if entries:
            data[filepath] = entries

    write_baseline(data, path)


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


def _build_lookup(data: BaselineData) -> dict[str, frozenset[tuple[str, str]]]:
    """Pre-process baseline data into a fast lookup structure.

    Returns a dict mapping file path str to a frozenset of (symbol, code).
    """
    lookup: dict[str, frozenset[tuple[str, str]]] = {}
    for filepath, entries in data.items():
        lookup[filepath] = frozenset(
            (e["symbol"], e["code"]) for e in entries if isinstance(e, dict) and "symbol" in e and "code" in e
        )
    return lookup


def filter_baseline_violations(
    diagnostics: list[Diagnostic],
    baseline: BaselineData,
    filepath: str,
    *,
    prebuilt_lookup: dict[str, frozenset[tuple[str, str]]] | None = None,
) -> list[Diagnostic]:
    """Return only diagnostics that are *not* present in the baseline.

    A diagnostic is considered "in the baseline" when the (symbol, code) pair
    for its file appears in the loaded baseline data.

    *prebuilt_lookup* may be supplied to avoid rebuilding the lookup structure
    on each call when filtering multiple files against the same baseline.
    Use ``_build_lookup(baseline)`` to pre-compute it.
    """
    if not baseline:
        return diagnostics

    lookup = prebuilt_lookup if prebuilt_lookup is not None else _build_lookup(baseline)
    baseline_pairs = lookup.get(filepath, frozenset())
    if not baseline_pairs:
        return diagnostics

    return [d for d in diagnostics if (d.symbol, d.rule) not in baseline_pairs]


# ---------------------------------------------------------------------------
# Auto-regeneration
# ---------------------------------------------------------------------------


def compute_updated_baseline(
    baseline: BaselineData,
    actual_violations_by_file: dict[str, list[Diagnostic]],
) -> tuple[bool, BaselineData]:
    """Compute an updated baseline that removes violations already fixed.

    Compares the loaded *baseline* against the *actual_violations_by_file*
    found in the current run.  Any baseline entry whose (symbol, code) is no
    longer present in the actual violations is considered fixed and removed.

    Returns ``(changed, updated_baseline)`` where *changed* is True when the
    baseline needs to be rewritten.
    """
    updated: BaselineData = {}
    changed = False

    for filepath, entries in baseline.items():
        actual = actual_violations_by_file.get(filepath, [])
        actual_pairs = frozenset((d.symbol, d.rule) for d in actual)

        remaining = [e for e in entries if (e.get("symbol", ""), e.get("code", "")) in actual_pairs]
        if len(remaining) != len(entries):
            changed = True
        if remaining:
            updated[filepath] = remaining

    return changed, updated
