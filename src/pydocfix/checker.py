"""Source file checker — orchestrates parsing and diagnosis."""

from __future__ import annotations

import ast
import dataclasses
import logging
import re
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path
from typing import Final, NamedTuple

import pydocstring
from pydocstring import (
    GoogleDocstring,
    NumPyDocstring,
    PlainDocstring,
    Visitor,
)

from pydocfix.config import Config
from pydocfix.noqa import NoqaDirective, find_inline_noqa, parse_file_noqa
from pydocfix.rules import (
    ALL_RULE_CODES,
    BaseRule,
    DiagnoseContext,
    Diagnostic,
    DocstringLocation,
    Edit,
    Fix,
    Offset,
    Range,
    apply_edits,
    is_applicable,
)

logger = logging.getLogger(__name__)


class _DocstringInfo(NamedTuple):
    """Extracted info about a docstring from source."""

    content: str
    stmt: ast.stmt
    parent: ast.AST


def _extract_docstrings(source: str, filepath: Path, tree: ast.AST | None = None) -> Iterator[_DocstringInfo]:
    """Yield `_DocstringInfo` for every docstring in *source*.

    If *tree* is provided it is used directly; otherwise the source is parsed.
    Sharing a pre-parsed tree with callers ensures ``id()``-based lookups stay
    consistent across the same AST instance.
    """
    if tree is None:
        try:
            tree = ast.parse(source, filename=str(filepath))
        except SyntaxError:
            logger.warning(f"{filepath}: could not parse (syntax error), skipping")
            return

    for node in ast.walk(tree):
        try:
            docstr: Final[str | None] = ast.get_docstring(node, clean=False)  # type: ignore
        except TypeError:
            continue  # node cannot have a docstring

        if docstr is None:
            continue  # node has no docstring

        yield _DocstringInfo(
            docstr,
            node.body[0],  # type: ignore
            node,
        )


_REGEX_OPENING_QUOTES: Final = re.compile(r"(?P<prefix>[rRuUfFbB]{0,2})(?P<quote>\"\"\"|\'{3}|\"|\')")


def _locate_docstring(
    ds_stmt: ast.stmt,
    lines: Sequence[str],
    line_offsets: Sequence[int],
    source_bytes: bytes,
) -> DocstringLocation | None:
    """Compute all positional info for a docstring expression at once.

    Returns None if the opening quote cannot be located.
    """
    start_line: Final[str] = lines[ds_stmt.lineno - 1]
    matched: Final[re.Match[str] | None] = _REGEX_OPENING_QUOTES.match(start_line, pos=ds_stmt.col_offset)
    if matched is None:
        logger.warning("could not locate opening quote at line %d", ds_stmt.lineno)
        return None

    quote_chars: Final[str] = matched.group("quote")

    if ds_stmt.end_lineno is None or ds_stmt.end_col_offset is None:
        logger.warning("could not determine end position at line %d", ds_stmt.lineno)
        return None

    # Byte range of the entire expression in source
    byte_start: Final[int] = line_offsets[ds_stmt.lineno - 1] + ds_stmt.col_offset
    byte_end: Final[int] = line_offsets[ds_stmt.end_lineno - 1] + ds_stmt.end_col_offset

    # Extract closing quote directly from pre-encoded source bytes
    closing: Final[str] = source_bytes[byte_end - len(quote_chars) : byte_end].decode("ascii")

    return DocstringLocation(
        content_start=Offset(ds_stmt.lineno, matched.end()),
        expr_byte_start=byte_start,
        expr_byte_end=byte_end,
        opening_quote=matched.group(0),
        closing_quote=closing,
    )


def build_rules_map(rules: Iterable[BaseRule]) -> dict[type, list[BaseRule]]:
    """Build cst->rules dispatch map."""
    kind_map: dict[type, list[BaseRule]] = {}
    for rule in rules:
        for kind in rule.target_kinds:
            kind_map.setdefault(kind, []).append(rule)
    return kind_map


def _has_overlap(accepted: Iterable[Edit], candidate: Fix) -> bool:
    """Return True if any edit in *candidate* overlaps with *accepted* edits."""
    for new in candidate.edits:
        for existing in accepted:
            if new.start < existing.end and existing.start < new.end:
                return True
    return False


class _RuleVisitor(Visitor):
    """Walk the CST and collect diagnostics from matching rules."""

    def __init__(
        self,
        kind_map: dict[type, list[BaseRule]],
        filepath: Path,
        ds_content: str,
        parsed: GoogleDocstring | NumPyDocstring | PlainDocstring,
        parent_ast: ast.AST,
        ds_stmt: ast.stmt,
        ds_loc: DocstringLocation,
        config: Config | None,
    ) -> None:
        self._kind_map = kind_map
        self._filepath = filepath
        self._ds_content = ds_content
        self._parsed = parsed
        self._parent_ast = parent_ast
        self._ds_stmt = ds_stmt
        self._ds_loc = ds_loc
        self._config = config
        self.diagnostics: list[Diagnostic] = []
        # Track current section's entries for context
        self._current_section_entries: list = []

    def _dispatch(self, node, section_entries=None):
        """Dispatch a node to matching rules."""
        matching = self._kind_map.get(type(node), [])
        if not matching:
            return
        ctx = DiagnoseContext(
            filepath=self._filepath,
            docstring_text=self._ds_content,
            docstring_cst=self._parsed,
            target_cst=node,
            parent_ast=self._parent_ast,
            docstring_stmt=self._ds_stmt,
            docstring_location=self._ds_loc,
            config=self._config,
            section_entries=section_entries or [],
        )
        for rule in matching:
            self.diagnostics.extend(rule.diagnose(ctx))

    # Google style
    def enter_google_docstring(self, node, ctx):
        self._dispatch(node)

    def enter_google_section(self, node, ctx):
        self._dispatch(node)

    def enter_google_arg(self, node, ctx):
        self._dispatch(node)

    def enter_google_return(self, node, ctx):
        self._dispatch(node)

    def enter_google_exception(self, node, ctx):
        self._dispatch(node)

    def enter_google_yield(self, node, ctx):
        self._dispatch(node)

    def enter_google_attribute(self, node, ctx):
        self._dispatch(node)

    def enter_google_warning(self, node, ctx):
        self._dispatch(node)

    def enter_google_see_also_item(self, node, ctx):
        self._dispatch(node)

    def enter_google_method(self, node, ctx):
        self._dispatch(node)

    # NumPy style
    def enter_numpy_docstring(self, node, ctx):
        self._dispatch(node)

    def enter_numpy_section(self, node, ctx):
        self._dispatch(node)

    def enter_numpy_parameter(self, node, ctx):
        self._dispatch(node)

    def enter_numpy_returns(self, node, ctx):
        self._dispatch(node)

    def enter_numpy_exception(self, node, ctx):
        self._dispatch(node)

    def enter_numpy_yields(self, node, ctx):
        self._dispatch(node)

    def enter_numpy_attribute(self, node, ctx):
        self._dispatch(node)

    def enter_numpy_deprecation(self, node, ctx):
        self._dispatch(node)

    def enter_numpy_warning(self, node, ctx):
        self._dispatch(node)

    def enter_numpy_see_also_item(self, node, ctx):
        self._dispatch(node)

    def enter_numpy_reference(self, node, ctx):
        self._dispatch(node)

    def enter_numpy_method(self, node, ctx):
        self._dispatch(node)

    # Plain
    def enter_plain_docstring(self, node, ctx):
        self._dispatch(node)


_MAX_FIX_ITERATIONS: Final[int] = 10
"""Maximum number of fix iterations per docstring before giving up."""


def _diagnose_docstring(
    kind_map: dict[type, list[BaseRule]],
    filepath: Path,
    ds_content: str,
    ds_stmt: ast.stmt,
    ds_loc: DocstringLocation,
    parent_ast: ast.AST,
    config: Config | None,
) -> list[Diagnostic]:
    """Parse and diagnose a single docstring, returning diagnostics."""
    parsed = pydocstring.parse(ds_content)
    collector = _RuleVisitor(
        kind_map=kind_map,
        filepath=filepath,
        ds_content=ds_content,
        parsed=parsed,
        parent_ast=parent_ast,
        ds_stmt=ds_stmt,
        ds_loc=ds_loc,
        config=config,
    )
    pydocstring.walk(parsed, collector)
    return collector.diagnostics


def _apply_nonoverlapping_fixes(
    ds_content: str,
    ds_diagnostics: list[Diagnostic],
    unsafe_fixes: bool,
    config: Config | None = None,
) -> tuple[str | None, int]:
    """Apply non-overlapping fixes to a docstring.

    Returns (new_content_or_none, count_of_applied_fixes).
    """
    accepted_edits: list[Edit] = []
    applied = 0
    for d in ds_diagnostics:
        if not is_applicable(d, unsafe_fixes, config):
            continue
        assert d.fix is not None
        if _has_overlap(accepted_edits, d.fix):
            logger.warning(
                "skipping fix from rule %s (overlapping edits)",
                d.rule,
            )
            continue
        accepted_edits.extend(d.fix.edits)
        applied += 1

    if not accepted_edits:
        return None, 0
    content = apply_edits(ds_content, accepted_edits)
    # When multiple sections are appended simultaneously to a single-line
    # docstring, each edit adds a trailing "\n<indent>" that becomes a
    # whitespace-only line immediately before the next section's "\n\n"
    # separator.  Normalize "\n<whitespace-only line>\n\n" → "\n\n".
    # Guard: only normalise when the *original* content had no newlines — that
    # is, it was a single-line docstring.  For multiline docstrings the
    # section-insertion edits are non-overlapping (multiline path in
    # section_append_edit), so the artifact never occurs and running the
    # substitution could incorrectly remove legitimate whitespace-only lines
    # (e.g. inside a code-example block with trailing spaces before a blank
    # line).
    if "\n" not in ds_content:
        content = re.sub(r"\n[ \t]+\n\n", "\n\n", content)
    return content, applied


def _compute_symbol(parent_ast: ast.AST, parent_map: dict[int, ast.AST]) -> str:
    """Return a qualified symbol name for the node that owns a docstring.

    Examples: ``"MyClass.my_method"``, ``"top_level_func"``, ``"MyClass"``.
    Returns an empty string for module-level docstrings.
    """
    if isinstance(parent_ast, (ast.FunctionDef, ast.AsyncFunctionDef)):
        name: str = parent_ast.name
        owner = parent_map.get(id(parent_ast))
        if isinstance(owner, ast.ClassDef):
            return f"{owner.name}.{name}"
        return name
    if isinstance(parent_ast, ast.ClassDef):
        return parent_ast.name
    return ""  # ast.Module or unexpected


def _build_parent_map(tree: ast.AST) -> dict[int, ast.AST]:
    """Return a mapping from ``id(child)`` to the child's direct parent node."""
    parent_map: dict[int, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parent_map[id(child)] = node
    return parent_map


def _check_unused_inline_noqa(
    *,
    inline_noqa: NoqaDirective,
    noqa_span: tuple[int, int],
    used_codes: set[str],
    any_suppressed: bool,
    end_lineno: int,
    lines: Sequence[str],
    line_offsets: Sequence[int],
    filepath: Path,
) -> tuple[list[Diagnostic], tuple[int, int, bytes] | None]:
    """Return NOQ001 diagnostics and an optional source edit for unused noqa codes.

    *used_codes*: pydocfix codes that actually suppressed at least one diagnostic.
    *any_suppressed*: True if the blanket noqa suppressed at least one diagnostic.
    *noqa_span*: ``(start, end)`` character positions of the match in the closing line.

    Codes not in ``ALL_RULE_CODES`` (e.g. other tools' codes) are ignored so that
    suppression comments like ``# noqa: PRM001, pylint-disable`` are handled safely.
    """
    if end_lineno <= 0 or end_lineno > len(lines):
        return [], None

    line = lines[end_lineno - 1]
    char_start, char_end = noqa_span
    line_byte_offset = line_offsets[end_lineno - 1]

    def _byte_pos(char_pos: int) -> int:
        return line_byte_offset + len(line[:char_pos].encode("utf-8"))

    diagnostics: list[Diagnostic] = []
    source_edit: tuple[int, int, bytes] | None = None

    if inline_noqa.codes is None:
        # Blanket # noqa — unused when nothing was suppressed
        if not any_suppressed:
            diagnostics.append(
                Diagnostic(
                    rule="NOQ001",
                    message="Unused `noqa` directive",
                    filepath=str(filepath),
                    range=Range(
                        start=Offset(end_lineno, char_start + 1),
                        end=Offset(end_lineno, char_end + 1),
                    ),
                )
            )
            ws_start = char_start
            while ws_start > 0 and line[ws_start - 1] in " \t":
                ws_start -= 1
            source_edit = (_byte_pos(ws_start), _byte_pos(char_end), b"")
    else:
        # Specific codes: flag each known-but-unused pydocfix code
        unused_known = (inline_noqa.codes & ALL_RULE_CODES) - used_codes
        if unused_known:
            for code in sorted(unused_known):
                diagnostics.append(
                    Diagnostic(
                        rule="NOQ001",
                        message=f"Unused `noqa` directive for {code}",
                        filepath=str(filepath),
                        range=Range(
                            start=Offset(end_lineno, char_start + 1),
                            end=Offset(end_lineno, char_end + 1),
                        ),
                    )
                )
            remaining_codes = inline_noqa.codes - unused_known
            if remaining_codes:
                # Rewrite the comment keeping used + non-pydocfix codes
                new_codes_str = ", ".join(sorted(remaining_codes))
                replacement = f"# noqa: {new_codes_str}".encode()
                source_edit = (_byte_pos(char_start), _byte_pos(char_end), replacement)
            else:
                # All codes remove — strip the entire comment
                ws_start = char_start
                while ws_start > 0 and line[ws_start - 1] in " \t":
                    ws_start -= 1
                source_edit = (_byte_pos(ws_start), _byte_pos(char_end), b"")

    return diagnostics, source_edit


def check_file(
    source: str,
    filepath: Path,
    kind_map: dict[type, list[BaseRule]],
    *,
    fix: bool = False,
    unsafe_fixes: bool = False,
    config: Config | None = None,
) -> tuple[list[Diagnostic], str | None, list[Diagnostic]]:
    """Diagnose and optionally fix all docstrings, iterating until stable.

    Returns (all_diagnostics, fixed_source_or_none, remaining_after_fix).
    *remaining_after_fix* is the list of diagnostics that still exist after
    all fixes have been applied (empty when fix=False).
    """
    lines: Final[list[str]] = source.splitlines(keepends=True)
    source_bytes: Final[bytes] = source.encode("utf-8")
    # Build line-start byte-offset table by scanning the byte string once
    line_offsets: Final[list[int]] = [0]
    pos = -1
    while (pos := source_bytes.find(b"\n", pos + 1)) != -1:
        line_offsets.append(pos + 1)
    file_noqa: Final[NoqaDirective | None] = parse_file_noqa(lines)
    all_diagnostics: list[Diagnostic] = []
    remaining_after_fix: list[Diagnostic] = []
    file_edits: list[tuple[int, int, bytes]] = []

    # Build parent map once for symbol computation
    parent_map: dict[int, ast.AST]
    try:
        _tree: ast.AST | None = ast.parse(source, filename=str(filepath))
        parent_map = _build_parent_map(_tree)
    except SyntaxError:
        _tree = None
        parent_map = {}

    for ds_content, ds_stmt, parent_ast in _extract_docstrings(source, filepath, _tree):
        # Determine where the docstring content starts (after opening triple-quote).
        ds_loc = _locate_docstring(ds_stmt, lines, line_offsets, source_bytes)
        if ds_loc is None:
            continue

        ds_diagnostics = _diagnose_docstring(
            kind_map,
            filepath,
            ds_content,
            ds_stmt,
            ds_loc,
            parent_ast,
            config,
        )

        # Apply noqa suppression before reporting or fixing
        inline_noqa: NoqaDirective | None = None
        inline_noqa_span: tuple[int, int] | None = None
        end_line_idx = (ds_stmt.end_lineno or 0) - 1
        if 0 <= end_line_idx < len(lines):
            found = find_inline_noqa(lines[end_line_idx])
            if found is not None:
                inline_noqa, inline_noqa_span = found

        used_inline: set[str] = set()
        inline_suppressed_any: bool = False
        if inline_noqa is not None or file_noqa is not None:
            kept: list[Diagnostic] = []
            for d in ds_diagnostics:
                suppress_inline = inline_noqa is not None and inline_noqa.suppresses(d.rule)
                suppress_file = file_noqa is not None and file_noqa.suppresses(d.rule)
                if suppress_inline or suppress_file:
                    if suppress_inline:
                        inline_suppressed_any = True
                        if inline_noqa is not None and inline_noqa.codes is not None:
                            used_inline.add(d.rule)
                else:
                    kept.append(d)
            ds_diagnostics = kept

        # Attach symbol to each diagnostic for baseline support
        symbol = _compute_symbol(parent_ast, parent_map)
        ds_diagnostics = [dataclasses.replace(d, symbol=symbol) for d in ds_diagnostics]

        all_diagnostics.extend(ds_diagnostics)

        # Fix phase (per-docstring) — iterate until stable
        if fix and ds_diagnostics:
            current_content = ds_content

            for _iteration in range(_MAX_FIX_ITERATIONS):
                new_content, applied = _apply_nonoverlapping_fixes(
                    current_content,
                    ds_diagnostics,
                    unsafe_fixes,
                    config,
                )
                if new_content is None:
                    break  # nothing fixable remains
                current_content = new_content

                # Re-diagnose the fixed docstring, re-annotate symbol
                ds_diagnostics = _diagnose_docstring(
                    kind_map,
                    filepath,
                    current_content,
                    ds_stmt,
                    ds_loc,
                    parent_ast,
                    config,
                )
                ds_diagnostics = [dataclasses.replace(d, symbol=symbol) for d in ds_diagnostics]
                if not ds_diagnostics or not any(is_applicable(d, unsafe_fixes, config) for d in ds_diagnostics):
                    break  # converged — no more fixable diagnostics
            else:
                logger.warning(
                    "%s: fix did not converge after %d iterations, stopping",
                    filepath,
                    _MAX_FIX_ITERATIONS,
                )

            # The final ds_diagnostics is the ground truth of what remains
            remaining_after_fix.extend(ds_diagnostics)

            if current_content != ds_content:
                file_edits.append(
                    (
                        ds_loc.expr_byte_start,
                        ds_loc.expr_byte_end,
                        (ds_loc.opening_quote + current_content + ds_loc.closing_quote).encode("utf-8"),
                    ),
                )

        # Generate NOQ001 diagnostics for unused inline noqa codes
        if inline_noqa is not None and inline_noqa_span is not None:
            noq_diagnostics, noq_source_edit = _check_unused_inline_noqa(
                inline_noqa=inline_noqa,
                noqa_span=inline_noqa_span,
                used_codes=used_inline,
                any_suppressed=inline_suppressed_any,
                end_lineno=ds_stmt.end_lineno or 0,
                lines=lines,
                line_offsets=line_offsets,
                filepath=filepath,
            )
            if noq_diagnostics:
                all_diagnostics.extend(noq_diagnostics)
                if fix and noq_source_edit is not None:
                    file_edits.append(noq_source_edit)
                    # NOQ001 was fixed — does not appear in remaining_after_fix
                elif fix:
                    # NOQ001 not fixable — still remains
                    remaining_after_fix.extend(noq_diagnostics)

    fixed_source: str | None = None
    if file_edits:
        buf = source_bytes
        for start, end, replacement in sorted(file_edits, key=lambda t: t[0], reverse=True):
            buf = buf[:start] + replacement + buf[end:]
        fixed_source = buf.decode("utf-8")

    return all_diagnostics, fixed_source, remaining_after_fix
