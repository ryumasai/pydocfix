"""Data types shared across the rule infrastructure."""

from __future__ import annotations

import enum
from dataclasses import dataclass


class Applicability(enum.Enum):
    """Whether a fix can be applied safely."""

    SAFE = "safe"
    UNSAFE = "unsafe"


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
