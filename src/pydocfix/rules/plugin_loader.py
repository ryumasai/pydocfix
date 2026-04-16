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
        logger.error(f"Failed to import plugin module '{module_name}': {e}")
        raise

    rules: list[type[BaseRule]] = []
    for name, obj in inspect.getmembers(module, inspect.isclass):
        # Check if it's a BaseRule subclass (but not BaseRule itself)
        if issubclass(obj, BaseRule) and obj is not BaseRule:
            # Skip abstract classes
            if inspect.isabstract(obj):
                continue
            # Verify it has a non-empty code
            if not obj.code:
                logger.warning(f"Skipping rule class {obj.__name__} in {module_name}: missing 'code' attribute")
                continue
            rules.append(obj)
            logger.debug(f"Discovered rule {obj.code} from {module_name}")

    return rules


def discover_rules_in_package(package_name: str) -> list[type[BaseRule]]:
    """Recursively discover all BaseRule subclasses in a package.

    Args:
        package_name: Fully qualified package name (e.g., "my_package.rules").

    Returns:
        List of BaseRule subclass types found in the package and its subpackages.

    """
    from pydocfix.rules._base import BaseRule

    try:
        package = importlib.import_module(package_name)
    except ImportError as e:
        logger.error(f"Failed to import plugin package '{package_name}': {e}")
        return []

    rules: list[type[BaseRule]] = []

    # Get package path
    if hasattr(package, "__path__"):
        package_path = package.__path__
    else:
        logger.warning(f"{package_name} is not a package, treating as module")
        return discover_rules_in_module(package_name)

    # Walk through all modules in the package
    for importer, modname, ispkg in pkgutil.walk_packages(
        path=package_path,
        prefix=f"{package_name}.",
    ):
        try:
            discovered = discover_rules_in_module(modname)
            rules.extend(discovered)
        except ImportError:
            logger.warning(f"Failed to import {modname}, skipping")
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
    from pydocfix.rules._base import BaseRule

    if not path.exists():
        logger.error(f"Plugin path does not exist: {path}")
        return []

    if not path.is_dir():
        logger.error(f"Plugin path is not a directory: {path}")
        return []

    rules: list[type[BaseRule]] = []
    path_str = str(path.resolve())

    # Temporarily add to sys.path
    if path_str not in sys.path:
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
                    logger.debug(f"Could not import {module_name} from {path}: {e}")
                    continue
        finally:
            # Remove from sys.path
            if path_str in sys.path:
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

    """
    rules: list[type[BaseRule]] = []

    # Load from modules/packages
    if plugin_modules:
        for module_name in plugin_modules:
            try:
                # Try as package first, fall back to module
                discovered = discover_rules_in_package(module_name)
                if not discovered:
                    discovered = discover_rules_in_module(module_name)
                rules.extend(discovered)
                logger.info(f"Loaded {len(discovered)} rule(s) from plugin '{module_name}'")
            except Exception as e:
                logger.error(f"Failed to load plugin '{module_name}': {e}")

    # Load from paths
    if plugin_paths:
        for path in plugin_paths:
            try:
                discovered = discover_rules_in_path(path)
                rules.extend(discovered)
                logger.info(f"Loaded {len(discovered)} rule(s) from path '{path}'")
            except Exception as e:
                logger.error(f"Failed to load plugins from '{path}': {e}")

    # Check for duplicate codes
    seen_codes: dict[str, type[BaseRule]] = {}
    for rule_cls in rules:
        if rule_cls.code in seen_codes:
            existing = seen_codes[rule_cls.code]
            logger.warning(
                f"Duplicate rule code '{rule_cls.code}': "
                f"{existing.__module__}.{existing.__name__} and "
                f"{rule_cls.__module__}.{rule_cls.__name__}"
            )
        else:
            seen_codes[rule_cls.code] = rule_cls

    return rules
