"""Shared helpers for parameter-related rules."""

from __future__ import annotations

import ast

import pydocstring
from pydocstring import (
    GoogleArg,
    GoogleSection,
    GoogleSectionKind,
    NumPyParameter,
    NumPySection,
    NumPySectionKind,
    Visitor,
)


def bare_name(name: str) -> str:
    """Strip leading ``*`` or ``**`` from a parameter name."""
    return name.lstrip("*")


def is_param_section(section) -> bool:
    """Return True if *section* is an Args/Parameters section."""
    if isinstance(section, GoogleSection):
        return section.section_kind == GoogleSectionKind.ARGS
    if isinstance(section, NumPySection):
        return section.section_kind == NumPySectionKind.PARAMETERS
    return False


def get_param_name_token(node):
    """Return the name token for a GoogleArg or NumPyParameter node, or None."""
    if isinstance(node, GoogleArg):
        return node.name
    if isinstance(node, NumPyParameter):
        return node.names[0] if node.names else None
    return None


def get_signature_params(
    func: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[tuple[str, str | None]]:
    """Return ``(display_name, annotation_or_None)`` for each parameter, excluding ``self``/``cls``.

    ``display_name`` uses ``*args``/``**kwargs`` prefixed forms for varargs.
    """
    result: list[tuple[str, str | None]] = []
    all_positional = [*func.args.posonlyargs, *func.args.args]
    skip_first = bool(all_positional) and all_positional[0].arg in ("self", "cls")
    for i, arg in enumerate(all_positional):
        if i == 0 and skip_first:
            continue
        ann = ast.unparse(arg.annotation) if arg.annotation else None
        result.append((arg.arg, ann))
    if func.args.vararg:
        ann = ast.unparse(func.args.vararg.annotation) if func.args.vararg.annotation else None
        result.append((f"*{func.args.vararg.arg}", ann))
    for arg in func.args.kwonlyargs:
        ann = ast.unparse(arg.annotation) if arg.annotation else None
        result.append((arg.arg, ann))
    if func.args.kwarg:
        ann = ast.unparse(func.args.kwarg.annotation) if func.args.kwarg.annotation else None
        result.append((f"**{func.args.kwarg.arg}", ann))
    return result


def get_annotation_map(
    func: ast.FunctionDef | ast.AsyncFunctionDef,
) -> dict[str, str]:
    """Build a mapping of parameter name -> unparsed type annotation.

    Both bare names and prefixed names (``*args``, ``**kwargs``) are included.
    """
    result: dict[str, str] = {}
    for arg in (*func.args.args, *func.args.posonlyargs, *func.args.kwonlyargs):
        if arg.annotation is not None:
            result[arg.arg] = ast.unparse(arg.annotation)
    if func.args.vararg and func.args.vararg.annotation is not None:
        ann = ast.unparse(func.args.vararg.annotation)
        name = func.args.vararg.arg
        result[name] = ann
        result[f"*{name}"] = ann
    if func.args.kwarg and func.args.kwarg.annotation is not None:
        ann = ast.unparse(func.args.kwarg.annotation)
        name = func.args.kwarg.arg
        result[name] = ann
        result[f"**{name}"] = ann
    return result


def get_documented_param_nodes(parsed, section: GoogleSection | NumPySection) -> list[tuple[str, object]]:
    """Return ``(raw_name, node)`` pairs for params documented in *section*, in order."""
    result: list[tuple[str, object]] = []

    class _Collector(Visitor):
        def enter_google_arg(self, node, ctx):
            if node.range.start >= section.range.start and node.range.end <= section.range.end and node.name:
                result.append((node.name.text, node))

        def enter_numpy_parameter(self, node, ctx):
            if node.range.start >= section.range.start and node.range.end <= section.range.end and node.names:
                result.append((node.names[0].text, node))

    pydocstring.walk(parsed, _Collector())
    return result
