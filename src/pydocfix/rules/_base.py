"""Shared infrastructure for linting rules."""

from __future__ import annotations

import ast
import enum
from collections import defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from itertools import pairwise
from typing import TYPE_CHECKING, Any, Final, NamedTuple

from pydocstring import (
    GoogleDocstring,
    NumPyDocstring,
    PlainDocstring,
    Token,
)

if TYPE_CHECKING:
    from pathlib import Path

    from pydocfix.config import Config


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
    docstring_line: int = 0
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

    content_offset: Offset  # where content begins (after opening quote)
    byte_start: int  # byte offset of expression start in source
    byte_end: int  # byte offset of expression end in source
    opening: str  # opening quote string (including prefix like r, u)
    closing: str  # closing quote string


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
    target_cst: Any
    parent_ast: ast.AST
    docstring_stmt: ast.stmt
    docstring_location: DocstringLocation
    config: Config | None = None
    section_entries: list[Any] = field(default_factory=list)

    def cst_node_range(self, cst: Any = None) -> Range:
        """Convert a CST node/token byte range to a file-level Range."""
        if cst is None:
            cst = self.target_cst
        ds_offset: Final[Offset] = self.docstring_location.content_offset
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


def replace_token(token: Token, new_text: str) -> Edit:
    """Replace a token's entire text."""
    return Edit(start=token.range.start, end=token.range.end, new_text=new_text)


def insert_at(offset: int, text: str) -> Edit:
    """Insert text at a byte offset (no deletion)."""
    return Edit(start=offset, end=offset, new_text=text)


def delete_range(start: int, end: int) -> Edit:
    """Delete a byte range."""
    return Edit(start=start, end=end, new_text="")


def detect_section_indent(ds_text: str, stmt_col_offset: int = 0) -> str:
    """Detect the section-level indentation from docstring content.

    For multiline docstrings the last line is typically only whitespace
    (the indent before the closing triple-quote) and directly gives the
    section indent.  Otherwise the first non-empty indented line after the
    summary is used, falling back to *stmt_col_offset* spaces.
    """
    lines = ds_text.split("\n")
    if len(lines) > 1:
        last = lines[-1]
        if not last.strip():
            return last
        for line in lines[1:]:
            if line and not line.isspace():
                n = len(line) - len(line.lstrip(" \t"))
                if n > 0:
                    return line[:n]
    return " " * stmt_col_offset


def section_append_edit(ds_text: str, root_end: int, section_text: str) -> Edit:
    """Build an Edit that appends *section_text* as a new docstring section.

    *section_text* should contain the fully-indented section (header + entries)
    joined by ``\\n``, without any surrounding blank lines.

    For multiline docstrings (where content ends with ``\\n<indent>``) the
    trailing whitespace is replaced so that:

    * There is exactly one blank line before the new section.
    * The closing triple-quote stays at the original indentation column.

    For single-line docstrings *section_text* is simply appended with a
    two-blank-line separator.
    """
    ds_bytes = ds_text.encode("utf-8")
    last_nl = ds_bytes.rfind(b"\n")
    if last_nl != -1 and not ds_bytes[last_nl + 1 :].strip():
        trailing = ds_bytes[last_nl + 1 :].decode("utf-8")
        return Edit(
            start=last_nl + 1,
            end=root_end,
            new_text=f"\n{section_text}\n{trailing}",
        )
    # Single-line or no trailing whitespace — detect indent from section_text itself
    n = len(section_text) - len(section_text.lstrip(" \t"))
    indent = section_text[:n]
    return Edit(
        start=root_end,
        end=root_end,
        new_text=f"\n\n{section_text}\n{indent}",
    )


def apply_edits(source: str, edits: Iterable[Edit]) -> str:
    """Apply Edits to a docstring, in reverse-offset order.

    Edit offsets are UTF-8 byte positions (as returned by pydocstring-rs).
    """
    sorted_edits: Final[list[Edit]] = sorted(edits, key=lambda e: e.start, reverse=True)
    # Validate no overlaps
    for prev, curr in pairwise(sorted_edits):
        if curr.end > prev.start:
            msg = f"Overlapping edits: [{curr.start}:{curr.end}] and [{prev.start}:{prev.end}]"
            raise ValueError(msg)
    buf: bytes = source.encode("utf-8")
    for edit in sorted_edits:
        buf = buf[: edit.start] + edit.new_text.encode("utf-8") + buf[edit.end :]
    return buf.decode("utf-8")


def _matches_any(code: str, patterns: frozenset[str]) -> bool:
    """Return True if *code* matches any pattern (exact, prefix, or ``ALL``)."""
    return "ALL" in patterns or any(code == p or code.startswith(p) for p in patterns)


def effective_applicability(diag: Diagnostic, config: Config | None = None) -> Applicability:
    """Return the effective applicability of a diagnostic's fix, after config overrides."""
    assert diag.fix is not None
    applicability = diag.fix.applicability
    if config is not None:
        code = diag.rule.upper()
        safe_patterns = frozenset(c.upper() for c in config.extend_safe_fixes)
        if safe_patterns and _matches_any(code, safe_patterns):
            return Applicability.SAFE
        unsafe_patterns = frozenset(c.upper() for c in config.extend_unsafe_fixes)
        if unsafe_patterns and _matches_any(code, unsafe_patterns):
            return Applicability.UNSAFE
    return applicability


def is_applicable(diag: Diagnostic, unsafe_fixes: bool, config: Config | None = None) -> bool:
    """Return True if the diagnostic's fix should be applied."""
    if diag.fix is None:
        return False
    app = effective_applicability(diag, config)
    if app == Applicability.SAFE:
        return True
    if app == Applicability.UNSAFE and unsafe_fixes:  # noqa: SIM103
        return True
    return False


class ConfigRequirement(NamedTuple):
    """Conflict resolution condition for a rule.

    Specifies which ``Config`` attribute must equal one of the allowed values
    for the rule to win when it is in an active conflict
    (see ``BaseRule.conflicts_with``).
    """

    attr: str
    """Name of the ``Config`` attribute to inspect (e.g. ``"type_annotation_style"``)."""
    values: frozenset[str]
    """Allowed values of the attribute (e.g. ``frozenset({"signature"})``)."""


class BaseRule:
    """Base class for all linting rules."""

    code: str = ""
    message: str = ""
    enabled_by_default: bool = True
    target_kinds: frozenset[type] = frozenset()
    conflicts_with: frozenset[str] = frozenset()
    requires_config: ConfigRequirement | None = None

    def __init__(self, config: Config | None = None) -> None:
        self.config = config

    def diagnose(self, ctx: DiagnoseContext) -> Iterator[Diagnostic]:
        """Yield zero or more Diagnostics for the given context."""
        raise NotImplementedError

    def _make_diagnostic(
        self,
        ctx: DiagnoseContext,
        message: str,
        *,
        fix: Fix | None = None,
        target: Any = None,
    ) -> Diagnostic:
        """Helper to create a Diagnostic with correct filepath and range."""
        return Diagnostic(
            rule=self.code,
            message=message,
            filepath=str(ctx.filepath),
            range=ctx.cst_node_range(target),
            docstring_line=ctx.docstring_stmt.lineno,
            fix=fix,
        )


@dataclass
class RuleRegistry:
    """Manages available rules."""

    _rules: dict[str, BaseRule] = field(default_factory=dict)
    _by_kind: dict[type, list[BaseRule]] = field(default_factory=lambda: defaultdict(list))

    def register(self, rule: BaseRule) -> None:
        self._rules[rule.code] = rule
        for kind in rule.target_kinds:
            self._by_kind[kind].append(rule)

    def get(self, code: str) -> BaseRule | None:
        return self._rules.get(code)

    def rules_for_kind(self, kind: type) -> list[BaseRule]:
        return self._by_kind.get(kind, [])

    def all_rules(self) -> list[BaseRule]:
        return list(self._rules.values())

    @property
    def kind_map(self) -> dict[type, list[BaseRule]]:
        return dict(self._by_kind)
