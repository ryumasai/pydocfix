"""Shared infrastructure for linting rules.

This module provides the core abstractions (``BaseRule``, ``DiagnoseContext``)
and re-exports the public symbols from the split sub-modules so that existing
``from pydocfix.rules._base import X`` imports continue to work.
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

from pydocfix._types import (
    ActivationCondition as ActivationCondition,
)
from pydocfix._types import (
    Applicability as Applicability,
)
from pydocfix._types import (
    Diagnostic as Diagnostic,
)
from pydocfix._types import (
    DocstringLocation as DocstringLocation,
)
from pydocfix._types import (
    Edit as Edit,
)
from pydocfix._types import (
    Fix as Fix,
)
from pydocfix._types import (
    Offset as Offset,
)
from pydocfix._types import (
    Range as Range,
)
from pydocfix._types import (
    Severity as Severity,
)

# Re-export data types so existing imports keep working.
from pydocfix.rules._edits import (
    apply_edits as apply_edits,
)
from pydocfix.rules._edits import (
    delete_range as delete_range,
)
from pydocfix.rules._edits import (
    detect_section_indent as detect_section_indent,
)
from pydocfix.rules._edits import (
    insert_at as insert_at,
)
from pydocfix.rules._edits import (
    replace_token as replace_token,
)
from pydocfix.rules._edits import (
    section_append_edit as section_append_edit,
)
from pydocfix.rules._registry import (
    RuleRegistry as RuleRegistry,
)
from pydocfix.rules._registry import (
    _matches_any as _matches_any,
)
from pydocfix.rules._registry import (
    effective_applicability as effective_applicability,
)
from pydocfix.rules._registry import (
    is_applicable as is_applicable,
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
