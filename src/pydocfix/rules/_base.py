"""Core abstractions for linting rules.

This module provides ``BaseRule`` (the ABC all rules subclass) and
``DiagnoseContext`` (the data passed to each rule's ``diagnose`` method).
"""

from __future__ import annotations

import ast
import typing
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Final, Generic, TypeVar

from pydocstring import (
    GoogleDocstring,
    NumPyDocstring,
    PlainDocstring,
)

from pydocfix.models import (
    ActivationCondition,
    Diagnostic,
    DocstringLocation,
    Fix,
    Offset,
    Range,
)

if TYPE_CHECKING:
    from pathlib import Path

    from pydocfix.config import Config


def _byte_offset_to_line_col(text_bytes: bytes, offset: int) -> tuple[int, int]:
    """Convert a byte offset within docstring text to (1-based line, 1-based col)."""
    before = text_bytes[:offset]
    lineno = before.count(b"\n") + 1
    last_nl = before.rfind(b"\n")
    col = offset - (last_nl + 1) + 1
    return lineno, col


@dataclass
class DiagnoseContext:
    """Information passed to a rule's diagnose method."""

    filepath: Path
    docstring_text: str
    docstring_cst: GoogleDocstring | NumPyDocstring | PlainDocstring
    parent_ast: ast.AST
    docstring_stmt: ast.stmt
    docstring_location: DocstringLocation

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


T = TypeVar("T")


class BaseRule(ABC, Generic[T]):
    """Abstract base class for all linting rules."""

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
