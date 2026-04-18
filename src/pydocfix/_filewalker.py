"""File collection utilities for pydocfix."""

from __future__ import annotations

import fnmatch
import logging
import re
from pathlib import Path
from typing import Final

logger = logging.getLogger(__name__)

_SUFFIXES: Final = {".py", ".pyi"}


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Convert a glob pattern with ** support to a compiled regex.

    - ``**`` matches zero or more path components (including none).
    - ``*`` matches any sequence of characters except ``/``.
    - ``?`` matches any single character except ``/``.
    """
    stripped = pattern.rstrip("/")
    i = 0
    parts: list[str] = ["^"]
    while i < len(stripped):
        if stripped[i : i + 2] == "**":
            i += 2
            if i < len(stripped) and stripped[i] == "/":
                # **/  → zero or more path components followed by /
                parts.append("(?:.*/)?")
                i += 1
            else:
                # ** at end → anything
                parts.append(".*")
            continue
        if stripped[i] == "*":
            parts.append("[^/]*")
            i += 1
        elif stripped[i] == "?":
            parts.append("[^/]")
            i += 1
        else:
            parts.append(re.escape(stripped[i]))
            i += 1
    parts.append("$")
    return re.compile("".join(parts))


def collect_files(
    paths: list[str],
    exclude: frozenset[str] = frozenset(),
    root: Path | None = None,
) -> list[Path]:
    """Resolve paths to a flat list of Python files, skipping excluded directories.

    ``exclude`` entries may be:

    - Simple names (``__pycache__``, ``.venv``) — matched against the directory
      name using :func:`fnmatch.fnmatch`.
    - Glob patterns with ``/`` or ``**`` (e.g. ``tests/**/fixtures``) — matched
      against the path relative to *root*.
    """
    _root = (root or Path.cwd()).resolve()

    # Pre-compile patterns into two buckets for efficiency.
    simple_patterns: list[str] = []  # matched against entry.name
    path_patterns: list[re.Pattern[str]] = []  # matched against relative path
    for pat in exclude:
        stripped = pat.rstrip("/")
        if "/" in stripped or "**" in stripped:
            path_patterns.append(_glob_to_regex(stripped))
        else:
            simple_patterns.append(stripped)

    def _is_excluded(entry: Path) -> bool:
        for pat in simple_patterns:
            if fnmatch.fnmatch(entry.name, pat):
                return True
        if path_patterns:
            try:
                rel = entry.resolve().relative_to(_root).as_posix()
            except ValueError:
                rel = entry.as_posix()
            for compiled in path_patterns:
                if compiled.match(rel):
                    return True
        return False

    def _walk(directory: Path) -> list[Path]:
        found: list[Path] = []
        for entry in directory.iterdir():
            if entry.is_dir():
                if not _is_excluded(entry):
                    found.extend(_walk(entry))
            elif entry.is_file() and entry.suffix in _SUFFIXES:
                found.append(entry)
        return found

    result: list[Path] = []
    for p in paths:
        path = Path(p)
        if path.is_file() and path.suffix in _SUFFIXES:
            result.append(path)
        elif path.is_dir():
            result.extend(_walk(path))
        else:
            logger.warning("path not found or not a Python file: %s", p)

    # Avoid duplicate work when users pass overlapping paths (e.g. '.' and 'src').
    unique: list[Path] = []
    seen: set[str] = set()
    for path in result:
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique
