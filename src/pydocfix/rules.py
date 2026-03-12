"""Linting rules for docstrings."""

from __future__ import annotations

import ast
import enum
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from itertools import pairwise
from typing import TYPE_CHECKING, Final

from pydocstring import (
    GoogleDocstring,
    Node,
    NumPyDocstring,
    SyntaxKind,
    Token,
)

if TYPE_CHECKING:
    from pathlib import Path


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
    """A source position (1-based line, 0-based column)."""

    lineno: int
    col: int


@dataclass(frozen=True)
class Range:
    """Source location range (1-based lines, 0-based columns)."""

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

    @property
    def fixable(self) -> bool:
        return self.fix is not None

    @property
    def lineno(self) -> int:
        return self.range.start.lineno

    @property
    def col(self) -> int:
        return self.range.start.col


@dataclass
class DiagnoseContext:
    """Information passed to a rule's diagnose method."""

    filepath: Path
    docstring_text: str
    docstring_cst: GoogleDocstring | NumPyDocstring
    target_cst: Node | Token
    parent_ast: ast.AST
    docstring_stmt: ast.stmt
    docstring_text_offset: Offset

    def _build_line_offsets(self) -> list[int]:
        """Return a list mapping each line (0-indexed) to its byte offset."""
        offsets = [0]
        for i, ch in enumerate(self.docstring_text):
            if ch == "\n":
                offsets.append(i + 1)
        return offsets

    def cst_node_range(self, node: Node | Token | None = None) -> Range:
        """Convert a CST node/token byte range to a file-level Range."""
        if node is None:
            node = self.target_cst
        line_offsets = self._build_line_offsets()
        return Range(
            start=Offset(
                self._offset_to_line(node.range.start, line_offsets),
                self._offset_to_col(node.range.start, line_offsets),
            ),
            end=Offset(
                self._offset_to_line(node.range.end, line_offsets), self._offset_to_col(node.range.end, line_offsets)
            ),
        )

    def _offset_to_line(self, offset: int, line_offsets: list[int]) -> int:
        """Convert a byte offset to a 1-based file line number."""
        import bisect

        local_line = bisect.bisect_right(line_offsets, offset) - 1
        return self.docstring_text_offset.lineno + local_line

    def _offset_to_col(self, offset: int, line_offsets: list[int]) -> int:
        """Convert a byte offset to a 0-based file column number."""
        import bisect

        local_line = bisect.bisect_right(line_offsets, offset) - 1
        col_in_content = offset - line_offsets[local_line]
        if local_line == 0:
            return self.docstring_text_offset.col + col_in_content
        return col_in_content


def replace_token(token: Token, new_text: str) -> Edit:
    """Replace a token's entire text."""
    return Edit(start=token.range.start, end=token.range.end, new_text=new_text)


def insert_at(offset: int, text: str) -> Edit:
    """Insert text at a byte offset (no deletion)."""
    return Edit(start=offset, end=offset, new_text=text)


def delete_range(start: int, end: int) -> Edit:
    """Delete a byte range."""
    return Edit(start=start, end=end, new_text="")


def apply_edits(source: str, edits: Iterable[Edit]) -> str:
    """Apply Edits to a docstring, in reverse-offset order."""
    sorted_edits: Final = sorted(edits, key=lambda e: e.start, reverse=True)
    # Validate no overlaps
    for prev, curr in pairwise(sorted_edits):
        if curr.end > prev.start:
            msg = f"Overlapping edits: [{curr.start}:{curr.end}] and [{prev.start}:{prev.end}]"
            raise ValueError(msg)
    result = source
    for edit in sorted_edits:
        result = result[: edit.start] + edit.new_text + result[edit.end :]
    return result


class BaseRule:
    """Base class for all linting rules."""

    code: str = ""
    message: str = ""
    target_kinds: set[SyntaxKind] = set()

    def diagnose(self, ctx: DiagnoseContext) -> Diagnostic | None:
        raise NotImplementedError

    # Helper -----------------------------------------------------------

    def _make_diagnostic(
        self,
        ctx: DiagnoseContext,
        message: str,
        *,
        fix: Fix | None = None,
        target: Node | Token | None = None,
    ) -> Diagnostic:
        return Diagnostic(
            rule=self.code,
            message=message,
            filepath=str(ctx.filepath),
            range=ctx.cst_node_range(target),
            docstring_line=ctx.docstring_stmt.lineno,
            fix=fix,
        )


# ── Built-in rules ───────────────────────────────────────────────────


class D200(BaseRule):
    """Summary should end with a period."""

    code = "D200"
    message = "Summary should end with a period."
    target_kinds = {SyntaxKind.SUMMARY}

    def diagnose(self, ctx: DiagnoseContext) -> Diagnostic | None:
        token = ctx.target_cst
        assert isinstance(token, Token)
        text = token.text.strip()
        if text and not text.endswith("."):
            fix = Fix(
                edits=[insert_at(token.range.end, ".")],
                applicability=Applicability.SAFE,
            )
            return self._make_diagnostic(ctx, self.message, fix=fix)
        return None


class D401(BaseRule):
    """Docstring type does not match type hint."""

    code = "D401"
    message = "Docstring type does not match type hint."
    target_kinds = {
        SyntaxKind.GOOGLE_ARG,
        SyntaxKind.NUMPY_PARAMETER,
        SyntaxKind.GOOGLE_RETURNS,
        SyntaxKind.NUMPY_RETURNS,
    }

    def _get_annotation_map(self, ast_node: ast.AST) -> dict[str, str]:
        """Build a mapping of parameter name -> unparsed type annotation."""
        if not isinstance(ast_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return {}
        result: dict[str, str] = {}
        for arg in (
            *ast_node.args.args,
            *ast_node.args.posonlyargs,
            *ast_node.args.kwonlyargs,
        ):
            if arg.annotation is not None:
                result[arg.arg] = ast.unparse(arg.annotation)
        if ast_node.args.vararg and ast_node.args.vararg.annotation is not None:
            result[ast_node.args.vararg.arg] = ast.unparse(ast_node.args.vararg.annotation)
        if ast_node.args.kwarg and ast_node.args.kwarg.annotation is not None:
            result[ast_node.args.kwarg.arg] = ast.unparse(ast_node.args.kwarg.annotation)
        return result

    def _get_return_annotation(self, ast_node: ast.AST) -> str | None:
        """Return unparsed return type annotation, or None."""
        if not isinstance(ast_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return None
        if ast_node.returns is None:
            return None
        return ast.unparse(ast_node.returns)

    def _find_child_token(self, node: Node, kind: SyntaxKind) -> Token | None:
        """Find the first child token with the given kind."""
        for child in node.children:
            if isinstance(child, Token) and child.kind == kind:
                return child
        return None

    def diagnose(self, ctx: DiagnoseContext) -> Diagnostic | None:
        cst_node = ctx.target_cst
        if not isinstance(cst_node, Node):
            return None

        kind = cst_node.kind

        # ── Parameter type mismatch ──
        if kind in (SyntaxKind.GOOGLE_ARG, SyntaxKind.NUMPY_PARAMETER):
            name_token = self._find_child_token(cst_node, SyntaxKind.NAME)
            type_token = self._find_child_token(cst_node, SyntaxKind.TYPE)
            if name_token is None or type_token is None:
                return None

            ann_map = self._get_annotation_map(ctx.parent_ast)
            param_name = name_token.text.strip()
            hint_type = ann_map.get(param_name)
            if hint_type is None:
                return None

            doc_type = type_token.text.strip()
            if doc_type == hint_type:
                return None

            fix = Fix(
                edits=[replace_token(type_token, hint_type)],
                applicability=Applicability.UNSAFE,
            )
            message = (
                f"Docstring type '{doc_type}' does not match type hint '{hint_type}' for parameter '{param_name}'."
            )
            return self._make_diagnostic(ctx, message, fix=fix, target=type_token)
        if kind in (SyntaxKind.GOOGLE_RETURNS, SyntaxKind.NUMPY_RETURNS):
            ret_type_token = self._find_child_token(cst_node, SyntaxKind.RETURN_TYPE)
            if ret_type_token is None:
                return None

            hint_type = self._get_return_annotation(ctx.parent_ast)
            if hint_type is None:
                return None

            doc_type = ret_type_token.text.strip()
            if doc_type == hint_type:
                return None

            fix = Fix(
                edits=[replace_token(ret_type_token, hint_type)],
                applicability=Applicability.UNSAFE,
            )
            message = f"Docstring return type '{doc_type}' does not match type hint '{hint_type}'."
            return self._make_diagnostic(ctx, message, fix=fix, target=ret_type_token)

        return None


# ── Registry ─────────────────────────────────────────────────────────

_BUILTIN_RULES: list[type[BaseRule]] = [D200, D401]


@dataclass
class RuleRegistry:
    """Manages available rules."""

    _rules: dict[str, BaseRule] = field(default_factory=dict)
    _by_kind: dict[SyntaxKind, list[BaseRule]] = field(default_factory=lambda: defaultdict(list))

    def register(self, rule: BaseRule) -> None:
        self._rules[rule.code] = rule
        for kind in rule.target_kinds:
            self._by_kind[kind].append(rule)

    def get(self, code: str) -> BaseRule | None:
        return self._rules.get(code)

    def rules_for_kind(self, kind: SyntaxKind) -> list[BaseRule]:
        return self._by_kind.get(kind, [])

    def all_rules(self) -> list[BaseRule]:
        return list(self._rules.values())


def build_registry() -> RuleRegistry:
    """Create a registry populated with built-in rules."""
    registry = RuleRegistry()
    for cls in _BUILTIN_RULES:
        registry.register(cls())
    return registry
