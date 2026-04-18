"""Plugin loader for discovering and loading custom rules."""

from __future__ import annotations

import importlib
import inspect
import logging
import pkgutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydocfix.rules._base import BaseRule

logger = logging.getLogger(__name__)


def discover_rules_in_module(module_name: str) -> list[type[BaseRule]]:
    """Discover all BaseRule subclasses in a module.

    Args:
        module_name: Fully qualified module name (e.g., "my_package.pydocfix_rules").

    Returns:
        List of BaseRule subclass types found in the module.

    Raises:
        ImportError: If the module cannot be imported.

    """
    from pydocfix.rules._base import BaseRule

    try:
        module = importlib.import_module(module_name)
    except ImportError as e:
        logger.error("Failed to import plugin module '%s': %s", module_name, e)
        raise

    rules: list[type[BaseRule]] = []
    for _name, obj in inspect.getmembers(module, inspect.isclass):
        # Check if it's a BaseRule subclass (but not BaseRule itself)
        if issubclass(obj, BaseRule) and obj is not BaseRule:
            # Skip abstract classes
            if inspect.isabstract(obj):
                continue
            # Verify it has a non-empty code
            if not obj.code:
                logger.warning("Skipping rule class %s in %s: missing 'code' attribute", obj.__name__, module_name)
                continue
            rules.append(obj)
            logger.debug("Discovered rule %s from %s", obj.code, module_name)

    return rules


def discover_rules_in_package(package_name: str) -> list[type[BaseRule]]:
    """Recursively discover all BaseRule subclasses in a package.

    Args:
        package_name: Fully qualified package name (e.g., "my_package.rules").

    Returns:
        List of BaseRule subclass types found in the package and its subpackages.

    """
    try:
        package = importlib.import_module(package_name)
    except ImportError as e:
        logger.error("Failed to import plugin package '%s': %s", package_name, e)
        return []

    rules: list[type[BaseRule]] = []

    # Get package path
    if hasattr(package, "__path__"):
        package_path = package.__path__
    else:
        logger.warning("%s is not a package, treating as module", package_name)
        return discover_rules_in_module(package_name)

    # Walk through all modules in the package
    for _importer, modname, _ispkg in pkgutil.walk_packages(
        path=package_path,
        prefix=f"{package_name}.",
    ):
        try:
            discovered = discover_rules_in_module(modname)
            rules.extend(discovered)
        except ImportError:
            logger.warning("Failed to import %s, skipping", modname)
            continue

    return rules


def discover_rules_in_path(path: Path) -> list[type[BaseRule]]:
    """Discover all BaseRule subclasses in a directory by adding it to sys.path.

    Args:
        path: Directory path containing Python modules/packages with rules.

    Returns:
        List of BaseRule subclass types found.

    Note:
        This modifies sys.path temporarily. Use with caution.

    """
    if not path.exists():
        logger.error("Plugin path does not exist: %s", path)
        return []

    if not path.is_dir():
        logger.error("Plugin path is not a directory: %s", path)
        return []

    rules: list[type[BaseRule]] = []
    path_str = str(path.resolve())

    # Temporarily add to sys.path
    already_present = path_str in sys.path
    if not already_present:
        sys.path.insert(0, path_str)
    try:
        # Discover all Python files in the directory
        for py_file in path.rglob("*.py"):
            if py_file.name.startswith("_"):
                continue

            # Convert file path to module name
            rel_path = py_file.relative_to(path)
            module_parts = list(rel_path.parts[:-1]) + [rel_path.stem]
            module_name = ".".join(module_parts)

            try:
                discovered = discover_rules_in_module(module_name)
                rules.extend(discovered)
            except (ImportError, TypeError) as e:
                logger.debug("Could not import %s from %s: %s", module_name, path, e)
                continue
    finally:
        # Remove from sys.path only if we added it
        if not already_present and path_str in sys.path:
            sys.path.remove(path_str)

    return rules


def load_plugin_rules(
    plugin_modules: list[str] | None = None,
    plugin_paths: list[Path] | None = None,
) -> list[type[BaseRule]]:
    """Load all plugin rules from specified modules and paths.

    Args:
        plugin_modules: List of fully qualified module/package names.
        plugin_paths: List of directory paths to search for plugins.

    Returns:
        List of all discovered BaseRule subclass types.

    Duplicate-code precedence is deterministic:
    1) ``plugin_modules`` entries (in the given order)
    2) ``plugin_paths`` entries (in the given order)
    3) within the same source, lexicographically by fully-qualified class name

    """
    discovered_rules: list[tuple[tuple[int, int], type[BaseRule]]] = []

    # Load from modules/packages
    if plugin_modules:
        for module_index, module_name in enumerate(plugin_modules):
            try:
                # Try as package first, fall back to module
                discovered = discover_rules_in_package(module_name)
                if not discovered:
                    discovered = discover_rules_in_module(module_name)
                discovered_rules.extend(((0, module_index), rule_cls) for rule_cls in discovered)
                logger.info("Loaded %d rule(s) from plugin '%s'", len(discovered), module_name)
            except Exception as e:
                logger.error("Failed to load plugin '%s': %s", module_name, e)

    # Load from paths
    if plugin_paths:
        for path_index, path in enumerate(plugin_paths):
            try:
                discovered = discover_rules_in_path(path)
                discovered_rules.extend(((1, path_index), rule_cls) for rule_cls in discovered)
                logger.info("Loaded %d rule(s) from path '%s'", len(discovered), path)
            except Exception as e:
                logger.error("Failed to load plugins from '%s': %s", path, e)

    # Deduplicate by rule code using deterministic precedence.
    grouped_by_code: dict[str, list[tuple[tuple[int, int], type[BaseRule]]]] = {}
    for priority, rule_cls in discovered_rules:
        grouped_by_code.setdefault(rule_cls.code, []).append((priority, rule_cls))

    selected: list[tuple[tuple[int, int], type[BaseRule]]] = []
    for code, candidates in grouped_by_code.items():
        ordered = sorted(candidates, key=lambda x: (x[0][0], x[0][1], x[1].__module__, x[1].__name__))
        winner_priority, winner = ordered[0]
        for _priority, contender in ordered[1:]:
            logger.warning(
                "Duplicate rule code '%s': keeping %s.%s, ignoring %s.%s",
                code,
                winner.__module__,
                winner.__name__,
                contender.__module__,
                contender.__name__,
            )
        selected.append((winner_priority, winner))

    selected.sort(key=lambda x: (x[0][0], x[0][1], x[1].__module__, x[1].__name__))
    return [rule_cls for _priority, rule_cls in selected]
