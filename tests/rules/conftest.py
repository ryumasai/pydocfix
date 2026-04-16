"""Shared test fixtures and utilities for rule tests."""

from __future__ import annotations

import ast
from pathlib import Path

from pydocstring import parse_google, parse_numpy

from pydocfix.checker import check_file
from pydocfix.rules import BaseRule, DiagnoseContext, Diagnostic, DocstringLocation, Offset


def make_function_ast(source: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    """Parse source and return the first function definition."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return node
    raise ValueError(f"No function found in source: {source}")


def make_google_context(
    docstring: str,
    func_source: str,
    *,
    filepath: Path | str = Path("test.py"),
) -> DiagnoseContext:
    """Create a DiagnoseContext for Google-style docstring testing.

    Args:
        docstring: The docstring text to parse.
        func_source: Python source code containing a function definition.
        filepath: Path to use in the context.

    Returns:
        DiagnoseContext ready for rule testing.
    """
    parsed = parse_google(docstring)
    func_ast = make_function_ast(func_source)

    return DiagnoseContext(
        filepath=Path(filepath) if isinstance(filepath, str) else filepath,
        docstring_text=docstring,
        docstring_cst=parsed,
        parent_ast=func_ast,
        docstring_stmt=ast.Expr(value=ast.Constant(value=docstring)),
        docstring_location=DocstringLocation(
            start=Offset(lineno=1, col_offset=4),
            end_quote_offset=len(docstring),
            indent_size=4,
            start_quote='"""',
            end_quote='"""',
        ),
    )


def make_numpy_context(
    docstring: str,
    func_source: str,
    *,
    filepath: Path | str = Path("test.py"),
) -> DiagnoseContext:
    """Create a DiagnoseContext for NumPy-style docstring testing.

    Args:
        docstring: The docstring text to parse.
        func_source: Python source code containing a function definition.
        filepath: Path to use in the context.

    Returns:
        DiagnoseContext ready for rule testing.
    """
    parsed = parse_numpy(docstring)
    func_ast = make_function_ast(func_source)

    return DiagnoseContext(
        filepath=Path(filepath) if isinstance(filepath, str) else filepath,
        docstring_text=docstring,
        docstring_cst=parsed,
        parent_ast=func_ast,
        docstring_stmt=ast.Expr(value=ast.Constant(value=docstring)),
        docstring_location=DocstringLocation(
            start=Offset(lineno=1, col_offset=4),
            end_quote_offset=len(docstring),
            indent_size=4,
            start_quote='"""',
            end_quote='"""',
        ),
    )


def check_fixture_file(
    fixture_path: Path,
    rules: list[BaseRule],
    *,
    fix: bool = False,
    unsafe_fixes: bool = False,
) -> tuple[list[Diagnostic], str | None, str]:
    """Check a fixture file with given rules.

    Args:
        fixture_path: Path to the fixture file to check.
        rules: List of rule instances to apply.
        fix: Whether to apply fixes.
        unsafe_fixes: Whether to apply unsafe fixes.

    Returns:
        Tuple of (diagnostics, fixed_source, original_source).
    """
    from pydocfix.checker import build_rules_map

    source = fixture_path.read_text(encoding="utf-8")
    type_to_rules = build_rules_map(rules)
    diagnostics, fixed_source, _ = check_file(
        source,
        fixture_path,
        type_to_rules,
        fix=fix,
        unsafe_fixes=unsafe_fixes,
    )
    return diagnostics, fixed_source, source


def load_fixture(fixture_name: str, category: str) -> Path:
    """Load a fixture file by name.

    Args:
        fixture_name: Name of the fixture file (e.g., "prm001_violation_basic.py").
        category: Rule category (e.g., "prm", "rtn", "sum").

    Returns:
        Path to the fixture file.

    Example:
        >>> path = load_fixture("prm001_violation_basic.py", "prm")
        >>> diagnostics, fixed, source = check_fixture_file(path, [PRM001()])
    """
    fixture_dir = Path(__file__).parent / category / "fixtures"
    fixture_path = fixture_dir / fixture_name
    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture not found: {fixture_path}")
    return fixture_path
