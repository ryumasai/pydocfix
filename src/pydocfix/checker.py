"""Source file checker — orchestrates parsing and diagnosis."""

from __future__ import annotations

import ast
import logging
import re
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path
from typing import Final, NamedTuple

import pydocstring
from pydocstring import (
    GoogleArg,
    GoogleAttribute,
    GoogleDocstring,
    GoogleException,
    GoogleMethod,
    GoogleReturn,
    GoogleSectionKind,
    GoogleSeeAlsoItem,
    GoogleWarning,
    GoogleYield,
    NumPyAttribute,
    NumPyDocstring,
    NumPyException,
    NumPyMethod,
    NumPyParameter,
    NumPyReference,
    NumPyReturns,
    NumPySectionKind,
    NumPySeeAlsoItem,
    NumPyWarning,
    NumPyYields,
    PlainDocstring,
    Visitor,
)

from pydocfix.config import Config
from pydocfix.noqa import NoqaDirective, parse_file_noqa, parse_inline_noqa
from pydocfix.rules import (
    BaseRule,
    DiagnoseContext,
    Diagnostic,
    DocstringLocation,
    Edit,
    Fix,
    Offset,
    apply_edits,
    is_applicable,
)

logger = logging.getLogger(__name__)


class _DocstringInfo(NamedTuple):
    """Extracted info about a docstring from source."""

    content: str
    parent_node: ast.AST
    stmt: ast.stmt


def _extract_docstrings(source: str, filepath: Path) -> Iterator[_DocstringInfo]:
    """Yield `_DocstringInfo` for every docstring in *source*."""
    try:
        tree: Final[ast.AST] = ast.parse(source, filename=str(filepath))
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
            node,
            node.body[0],  # type: ignore
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
        content_offset=Offset(ds_stmt.lineno, matched.end()),
        byte_start=byte_start,
        byte_end=byte_end,
        opening=matched.group(0),
        closing=closing,
    )


# Mapping from CST node type to the section-level "parent" types,
# for use in entry-level dispatching.
_ENTRY_TYPE_TO_SECTION_KIND = {
    GoogleArg: GoogleSectionKind.ARGS,
    GoogleReturn: GoogleSectionKind.RETURNS,
    GoogleException: GoogleSectionKind.RAISES,
    GoogleYield: GoogleSectionKind.YIELDS,
    GoogleAttribute: GoogleSectionKind.ATTRIBUTES,
    GoogleWarning: GoogleSectionKind.WARNINGS,
    GoogleSeeAlsoItem: GoogleSectionKind.SEE_ALSO,
    GoogleMethod: GoogleSectionKind.METHODS,
    NumPyParameter: NumPySectionKind.PARAMETERS,
    NumPyReturns: NumPySectionKind.RETURNS,
    NumPyException: NumPySectionKind.RAISES,
    NumPyYields: NumPySectionKind.YIELDS,
    NumPyAttribute: NumPySectionKind.ATTRIBUTES,
    NumPyWarning: NumPySectionKind.WARNINGS,
    NumPySeeAlsoItem: NumPySectionKind.SEE_ALSO,
    NumPyReference: NumPySectionKind.REFERENCES,
    NumPyMethod: NumPySectionKind.METHODS,
}


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


class _DiagnosticCollector(Visitor):
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

    def _dispatch_summary_token(self, docstring):
        """Dispatch the summary Token for rules targeting Token."""
        if docstring.summary is None:
            return
        token = docstring.summary
        matching = self._kind_map.get(type(token), [])
        if not matching:
            return
        ctx = DiagnoseContext(
            filepath=self._filepath,
            docstring_text=self._ds_content,
            docstring_cst=self._parsed,
            target_cst=token,
            parent_ast=self._parent_ast,
            docstring_stmt=self._ds_stmt,
            docstring_location=self._ds_loc,
            config=self._config,
        )
        for rule in matching:
            self.diagnostics.extend(rule.diagnose(ctx))

    # Google style
    def enter_google_docstring(self, node, ctx):
        self._dispatch(node)
        self._dispatch_summary_token(node)

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
        self._dispatch_summary_token(node)

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
        self._dispatch_summary_token(node)


_MAX_FIX_ITERATIONS: Final[int] = 10
"""Maximum number of fix iterations per docstring before giving up."""


def _diagnose_docstring(
    kind_map: dict[type, list[BaseRule]],
    filepath: Path,
    ds_content: str,
    parent_ast: ast.AST,
    ds_stmt: ast.stmt,
    ds_loc: DocstringLocation,
    config: Config | None,
) -> list[Diagnostic]:
    """Parse and diagnose a single docstring, returning diagnostics."""
    parsed = pydocstring.parse(ds_content)
    collector = _DiagnosticCollector(
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
) -> tuple[str | None, int]:
    """Apply non-overlapping fixes to a docstring.

    Returns (new_content_or_none, count_of_applied_fixes).
    """
    accepted_edits: list[Edit] = []
    applied = 0
    for d in ds_diagnostics:
        if not is_applicable(d, unsafe_fixes):
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


def check_file(
    source: str,
    filepath: Path,
    kind_map: dict[type, list[BaseRule]],
    *,
    fix: bool = False,
    unsafe_fixes: bool = False,
    config: Config | None = None,
) -> tuple[list[Diagnostic], str | None, frozenset[int]]:
    """Diagnose and optionally fix all docstrings, iterating until stable.

    Returns (all_diagnostics, fixed_source_or_none, indices_of_fixed_diagnostics).
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
    fixed_indices: set[int] = set()
    file_edits: list[tuple[int, int, bytes]] = []

    for ds_content, parent_ast, ds_stmt in _extract_docstrings(source, filepath):
        # Determine where the docstring content starts (after opening triple-quote).
        ds_loc = _locate_docstring(ds_stmt, lines, line_offsets, source_bytes)
        if ds_loc is None:
            continue

        ds_diagnostics = _diagnose_docstring(
            kind_map,
            filepath,
            ds_content,
            parent_ast,
            ds_stmt,
            ds_loc,
            config,
        )

        # Apply noqa suppression before reporting or fixing
        inline_noqa: NoqaDirective | None = None
        if ds_stmt.end_lineno is not None and 0 < ds_stmt.end_lineno <= len(lines):
            inline_noqa = parse_inline_noqa(lines[ds_stmt.end_lineno - 1])
        if inline_noqa is not None or file_noqa is not None:
            ds_diagnostics = [
                d
                for d in ds_diagnostics
                if not (
                    (inline_noqa is not None and inline_noqa.suppresses(d.rule))
                    or (file_noqa is not None and file_noqa.suppresses(d.rule))
                )
            ]

        base_idx = len(all_diagnostics)
        all_diagnostics.extend(ds_diagnostics)

        # Fix phase (per-docstring) — iterate until stable
        if fix and ds_diagnostics:
            current_content = ds_content
            # Track which first-pass diagnostics have been fixed by rule identity
            first_pass_rules = {(base_idx + i, d.rule, d.range) for i, d in enumerate(ds_diagnostics)}

            for _iteration in range(_MAX_FIX_ITERATIONS):
                new_content, applied = _apply_nonoverlapping_fixes(
                    current_content,
                    ds_diagnostics,
                    unsafe_fixes,
                )
                if new_content is None:
                    break  # nothing fixable remains
                current_content = new_content

                # Re-diagnose the fixed docstring
                ds_diagnostics = _diagnose_docstring(
                    kind_map,
                    filepath,
                    current_content,
                    parent_ast,
                    ds_stmt,
                    ds_loc,
                    config,
                )
                if not ds_diagnostics or not any(is_applicable(d, unsafe_fixes) for d in ds_diagnostics):
                    break  # converged — no more fixable diagnostics
            else:
                logger.warning(
                    "%s: fix did not converge after %d iterations, stopping",
                    filepath,
                    _MAX_FIX_ITERATIONS,
                )

            # Determine which first-pass diagnostics were fixed:
            # any diagnostic from the first pass whose (rule, range) no longer appears
            remaining_ids = {(d.rule, d.range) for d in ds_diagnostics}
            for idx, rule, rng in first_pass_rules:
                if (rule, rng) not in remaining_ids:
                    fixed_indices.add(idx)

            if current_content != ds_content:
                file_edits.append(
                    (
                        ds_loc.byte_start,
                        ds_loc.byte_end,
                        (ds_loc.opening + current_content + ds_loc.closing).encode("utf-8"),
                    ),
                )

    fixed_source: str | None = None
    if file_edits:
        buf = source_bytes
        for start, end, replacement in sorted(file_edits, key=lambda t: t[0], reverse=True):
            buf = buf[:start] + replacement + buf[end:]
        fixed_source = buf.decode("utf-8")

    return all_diagnostics, fixed_source, frozenset(fixed_indices)
