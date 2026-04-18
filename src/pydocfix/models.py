"""Data types shared across the rule infrastructure."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import NamedTuple


class Severity(enum.Enum):
    """Severity level for diagnostics."""

    ERROR = "error"
    WARNING = "warning"
    HINT = "hint"


class Applicability(enum.Enum):
    """Whether a fix can be applied safely."""

    SAFE = "safe"
    UNSAFE = "unsafe"
    DISPLAY_ONLY = "display-only"


@dataclass(frozen=True)
class Offset:
    """A source position (1-based line, 1-based column)."""

    lineno: int
    col: int


@dataclass(frozen=True)
class Range:
    """Source location range (1-based lines, 1-based columns)."""

    start: Offset
    end: Offset


@dataclass(frozen=True)
class Edit:
    """A single text replacement within a docstring.

    Offsets are byte positions relative to the start of the docstring
    (including the opening triple-quotes).
    """

    start: int
    end: int
    new_text: str


@dataclass(frozen=True)
class Fix:
    """A set of edits that fix a diagnostic."""

    edits: list[Edit]
    applicability: Applicability


@dataclass(frozen=True)
class Diagnostic:
    """A single issue found in a docstring, optionally bundled with a fix."""

    rule: str
    message: str
    filepath: str
    range: Range
    severity: Severity = Severity.WARNING
    fix: Fix | None = None
    symbol: str = ""

    @property
    def fixable(self) -> bool:
        return self.fix is not None

    @property
    def lineno(self) -> int:
        return self.range.start.lineno

    @property
    def col(self) -> int:
        return self.range.start.col


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
