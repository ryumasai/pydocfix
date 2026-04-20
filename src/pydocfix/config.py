"""Configuration loader for pydocfix."""

from __future__ import annotations

import logging
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_EXCLUDE: frozenset[str] = frozenset(
    {
        ".git",
        ".svn",
        ".venv",
        "venv",
        ".tox",
        ".nox",
        "__pycache__",
        "__pypackages__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".eggs",
        "build",
        "dist",
        "node_modules",
        "site-packages",
    }
)


@dataclass
class Config:
    """Resolved pydocfix configuration."""

    skip_short_docstrings: bool = True
    type_annotation_style: str | None = None
    allow_optional_shorthand: bool = False
    preferred_style: str = "google"
    class_docstring_style: str | None = None
    ignore: list[str] = field(default_factory=list)
    select: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    extend_safe_fixes: list[str] = field(default_factory=list)
    extend_unsafe_fixes: list[str] = field(default_factory=list)
    baseline: str | None = None
    output_format: str = "full"
    plugin_modules: list[str] = field(default_factory=list)
    plugin_paths: list[str] = field(default_factory=list)
    plugin_config: dict[str, dict[str, Any]] = field(default_factory=dict)


def find_pyproject_toml(start: Path | None = None) -> Path | None:
    """Walk up from *start* (defaults to CWD) to locate pyproject.toml."""
    current = (start or Path.cwd()).resolve()
    for directory in [current, *current.parents]:
        candidate = directory / "pyproject.toml"
        if candidate.is_file():
            return candidate
    return None


def load_config(start: Path | None = None) -> Config:
    """Load ``[tool.pydocfix]`` from the nearest pyproject.toml.

    Falls back to defaults when no file is found or the section is absent.
    """
    toml_path = find_pyproject_toml(start)
    if toml_path is None:
        return Config()

    try:
        with toml_path.open("rb") as fh:
            data = tomllib.load(fh)
    except Exception:
        logger.warning("could not read %s, using defaults", toml_path)
        return Config()

    section: dict = data.get("tool", {}).get("pydocfix", {})

    ignore: list[str] = [str(code) for code in section.get("ignore", [])]
    select: list[str] = [str(code) for code in section.get("select", [])]
    type_annotation_style: str | None = section.get("type_annotation_style") or None
    if type_annotation_style is not None and type_annotation_style not in {"signature", "docstring", "both"}:
        logger.warning(
            "invalid type_annotation_style %r (expected 'signature', 'docstring', or 'both'); ignoring",
            type_annotation_style,
        )
        type_annotation_style = None
    preferred_style: str = section.get("preferred_style", "google").lower()
    if preferred_style not in {"google", "numpy"}:
        logger.warning(
            "invalid preferred_style %r (expected 'google' or 'numpy'); defaulting to 'google'",
            preferred_style,
        )
        preferred_style = "google"
    exclude: list[str] = [str(p) for p in section.get("exclude", [])]
    raw_ssd = section.get("skip_short_docstrings")
    skip_short_docstrings: bool = bool(raw_ssd) if raw_ssd is not None else True
    raw_aos = section.get("allow_optional_shorthand")
    allow_optional_shorthand: bool = bool(raw_aos) if raw_aos is not None else False
    class_docstring_style: str | None = section.get("class-docstring-style") or None
    if class_docstring_style is not None and class_docstring_style not in {"class", "init", "both"}:
        logger.warning(
            "invalid class-docstring-style %r (expected 'class', 'init', or 'both'); ignoring",
            class_docstring_style,
        )
        class_docstring_style = None
    baseline: str | None = section.get("baseline") or None
    extend_safe_fixes: list[str] = [str(c).upper() for c in section.get("extend-safe-fixes", [])]
    extend_unsafe_fixes: list[str] = [str(c).upper() for c in section.get("extend-unsafe-fixes", [])]
    plugin_modules: list[str] = [str(m) for m in section.get("plugin-modules", [])]
    plugin_paths: list[str] = [str(p) for p in section.get("plugin-paths", [])]
    raw_plugin_config = section.get("plugin-config", {})
    plugin_config: dict[str, dict[str, Any]] = (
        {k: dict(v) for k, v in raw_plugin_config.items() if isinstance(v, dict)}
        if isinstance(raw_plugin_config, dict)
        else {}
    )
    output_format: str = section.get("output-format", "full").lower()
    if output_format not in {"full", "concise"}:
        logger.warning(
            "invalid output-format %r (expected 'full' or 'concise'); defaulting to 'full'",
            output_format,
        )
        output_format = "full"
    return Config(
        ignore=ignore,
        select=select,
        type_annotation_style=type_annotation_style,
        preferred_style=preferred_style,
        class_docstring_style=class_docstring_style,
        exclude=exclude,
        skip_short_docstrings=skip_short_docstrings,
        allow_optional_shorthand=allow_optional_shorthand,
        baseline=baseline,
        extend_safe_fixes=extend_safe_fixes,
        extend_unsafe_fixes=extend_unsafe_fixes,
        output_format=output_format,
        plugin_modules=plugin_modules,
        plugin_paths=plugin_paths,
        plugin_config=plugin_config,
    )
