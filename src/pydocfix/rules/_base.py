"""Core abstractions for linting rules.

This module provides context types (``FunctionCtx``, ``ClassCtx``,
``ModuleCtx``), the ``@rule`` decorator, and ``make_diagnostic``.
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Final, NamedTuple, Protocol, cast

from pydocstring import (
    GoogleDocstring,
    NumPyDocstring,
    PlainDocstring,
)

from pydocfix.diagnostics import (
    Diagnostic,
    Fix,
    Offset,
    Range,
)

if TYPE_CHECKING:
    from pathlib import Path

    from pydocfix.config import Config

# ---------------------------------------------------------------------------
# Positional helpers
# ---------------------------------------------------------------------------


class DocstringLocation(NamedTuple):
    """Pre-computed positional info for a docstring expression."""

    content_start: Offset  # line:col where content begins (after opening quote)
    expr_byte_start: int  # byte offset of expression start in source file
    expr_byte_end: int  # byte offset of expression end in source file
    opening_quote: str  # opening quote string (including prefix like r, u)
    closing_quote: str  # closing quote string


class ActivationCondition(NamedTuple):
    """Config-based activation condition for a rule.

    Specifies which ``Config`` attribute must equal one of the allowed values
    for the rule to be active.
    """

    attr: str
    """Name of the ``Config`` attribute to inspect (e.g. ``"type_annotation_style"``)."""
    values: frozenset[str]
    """Allowed values of the attribute (e.g. ``frozenset({"signature"})``)."""


def _byte_offset_to_line_col(text_bytes: bytes, offset: int) -> tuple[int, int]:
    """Convert a byte offset within docstring text to (1-based line, 1-based col)."""
    before = text_bytes[:offset]
    lineno = before.count(b"\n") + 1
    last_nl = before.rfind(b"\n")
    col = offset - (last_nl + 1) + 1
    return lineno, col


# ---------------------------------------------------------------------------
# Context types
# ---------------------------------------------------------------------------


@dataclass
class BaseCtx:
    """Information passed to a rule function."""

    filepath: Path
    docstring_text: str
    docstring_cst: GoogleDocstring | NumPyDocstring | PlainDocstring
    docstring_location: DocstringLocation
    docstring_stmt: ast.stmt
    config: Config | None = None
    class_ast: ast.ClassDef | None = None

    def cst_node_range(self, cst: Any) -> Range:
        """Convert a CST node/token byte range to a file-level Range."""
        ds_offset: Final[Offset] = self.docstring_location.content_start
        ds_bytes: Final[bytes] = self.docstring_text.encode("utf-8")
        start_line, start_col = _byte_offset_to_line_col(ds_bytes, cst.range.start)
        end_line, end_col = _byte_offset_to_line_col(ds_bytes, cst.range.end)
        return Range(
            start=Offset(
                ds_offset.lineno + start_line - 1,
                ds_offset.col + start_col if start_line == 1 else start_col,
            ),
            end=Offset(
                ds_offset.lineno + end_line - 1,
                ds_offset.col + end_col if end_line == 1 else end_col,
            ),
        )


@dataclass
class FunctionCtx(BaseCtx):
    """Context for rules that target function/method docstrings."""

    parent: ast.FunctionDef | ast.AsyncFunctionDef = field(kw_only=True)


@dataclass
class ClassCtx(BaseCtx):
    """Context for rules that target class docstrings."""

    parent: ast.ClassDef = field(kw_only=True)


@dataclass
class ModuleCtx(BaseCtx):
    """Context for rules that target module docstrings."""

    parent: ast.Module = field(kw_only=True)


# ---------------------------------------------------------------------------
# @rule decorator
# ---------------------------------------------------------------------------

CtxType = type[FunctionCtx] | type[ClassCtx] | type[ModuleCtx]


class RuleFn(Protocol):
    """Callable protocol for ``@rule``-decorated functions."""

    _rule_code: str
    _enabled_by_default: bool
    _conflicts_with: frozenset[str]
    _activation_condition: ActivationCondition | None
    _ctx_types: frozenset[CtxType]
    _cst_types: frozenset[type]
    __qualname__: str
    __module__: str

    def __call__(self, *args: Any, **kwargs: Any) -> Iterator[Diagnostic]: ...


def rule(
    code: str,
    *,
    ctx_types: frozenset[CtxType],
    cst_types: frozenset[type],
    enabled_by_default: bool = True,
    conflicts_with: frozenset[str] = frozenset(),
    activation_condition: ActivationCondition | None = None,
):
    """Decorator that marks a function as a pydocfix rule."""

    def decorator(func: Callable[..., Iterator[Diagnostic]]) -> RuleFn:
        fn = cast(Any, func)
        fn._rule_code = code
        fn._enabled_by_default = enabled_by_default
        fn._conflicts_with = conflicts_with
        fn._activation_condition = activation_condition
        fn._ctx_types = ctx_types
        fn._cst_types = cst_types
        return cast(RuleFn, func)

    return decorator


# ---------------------------------------------------------------------------
# make_diagnostic helper
# ---------------------------------------------------------------------------


def make_diagnostic(
    code: str,
    ctx: BaseCtx,
    message: str,
    *,
    target: Any,
    fix: Fix | None = None,
) -> Diagnostic:
    """Create a Diagnostic with correct filepath and range."""
    return Diagnostic(
        rule=code,
        message=message,
        filepath=str(ctx.filepath),
        range=ctx.cst_node_range(target),
        fix=fix,
    )
