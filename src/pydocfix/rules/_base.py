"""Core abstractions for linting rules.

This module provides context types (``FunctionCtx``, ``ClassCtx``,
``ModuleCtx``), the ``@rule`` decorator, and ``make_diagnostic``.
"""

from __future__ import annotations

import ast
import typing
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Final, Generic, NamedTuple, TypeVar

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
# Type aliases
# ---------------------------------------------------------------------------

RuleFn = Callable[..., Iterator[Diagnostic]]


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

    parent: ast.FunctionDef | ast.AsyncFunctionDef = None  # type: ignore[assignment]


@dataclass
class ClassCtx(BaseCtx):
    """Context for rules that target class docstrings."""

    parent: ast.ClassDef = None  # type: ignore[assignment]


@dataclass
class ModuleCtx(BaseCtx):
    """Context for rules that target module docstrings."""

    parent: ast.Module = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Backward-compatible aliases
# ---------------------------------------------------------------------------

DiagnoseContext = BaseCtx


# ---------------------------------------------------------------------------
# @rule decorator
# ---------------------------------------------------------------------------

CtxType = type[FunctionCtx] | type[ClassCtx] | type[ModuleCtx]


def rule(
    code: str,
    *,
    targets: CtxType | tuple[CtxType, ...],
    cst_types: type | tuple[type, ...],
    enabled_by_default: bool = True,
    conflicts_with: frozenset[str] = frozenset(),
    activation_condition: ActivationCondition | None = None,
):
    """Decorator that marks a function as a pydocfix rule."""

    def decorator(func: RuleFn) -> RuleFn:
        func._rule_code = code  # type: ignore[attr-defined]
        func._enabled_by_default = enabled_by_default  # type: ignore[attr-defined]
        func._conflicts_with = conflicts_with  # type: ignore[attr-defined]
        func._activation_condition = activation_condition  # type: ignore[attr-defined]
        func._targets_ctx = frozenset(  # type: ignore[attr-defined]
            targets if isinstance(targets, tuple) else (targets,)
        )
        func._targets_cst = frozenset(  # type: ignore[attr-defined]
            cst_types if isinstance(cst_types, tuple) else (cst_types,)
        )
        return func

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


# ---------------------------------------------------------------------------
# Backward-compatible BaseRule class (for unconverted rules)
# ---------------------------------------------------------------------------

T = TypeVar("T")


class BaseRule(ABC, Generic[T]):
    """Abstract base class for class-based linting rules (legacy).

    New rules should use the ``@rule`` decorator instead.
    """

    code: str = ""
    enabled_by_default: bool = True
    conflicts_with: frozenset[str] = frozenset()
    activation_condition: ActivationCondition | None = None
    _targets: frozenset[type] = frozenset()

    def __init__(self, config: Config | None = None) -> None:
        self.config = config

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Detect the target CST node types from the generic parameter."""
        super().__init_subclass__(**kwargs)
        if not cls.code:
            raise TypeError(f"{cls.__name__} must define a non-empty 'code'")
        for base in getattr(cls, "__orig_bases__", ()):
            if typing.get_origin(base) is BaseRule:
                args = typing.get_args(base)
                if args:
                    t = args[0]
                    inner = typing.get_args(t)
                    cls._targets = frozenset(inner) if inner else frozenset({t})
                break

    def _make_diagnostic(
        self,
        ctx: DiagnoseContext,
        message: str,
        *,
        fix: Fix | None = None,
        target: Any,
    ) -> Diagnostic:
        """Create a Diagnostic with correct filepath and range."""
        return Diagnostic(
            rule=self.code,
            message=message,
            filepath=str(ctx.filepath),
            range=ctx.cst_node_range(target),
            fix=fix,
        )

    @abstractmethod
    def diagnose(self, node: T, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        """Yield zero or more Diagnostics for the given context."""
        ...
