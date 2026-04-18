"""Rule DOC002 - Incorrect indentation of a docstring section entry."""

from __future__ import annotations

from collections.abc import Iterator

from pydocstring import (
    GoogleArg,
    GoogleAttribute,
    GoogleException,
    GoogleMethod,
    GoogleReturn,
    GoogleSeeAlsoItem,
    GoogleWarning,
    GoogleYield,
    NumPyAttribute,
    NumPyException,
    NumPyMethod,
    NumPyParameter,
    NumPyReference,
    NumPyReturns,
    NumPySeeAlsoItem,
    NumPyWarning,
    NumPyYields,
)

from pydocfix._edits import detect_section_indent
from pydocfix._types import Applicability, Diagnostic, Edit, Fix
from pydocfix.rules._base import BaseRule, DiagnoseContext

_NUMPY_ENTRY_TYPES: frozenset[type] = frozenset(
    {
        NumPyParameter,
        NumPyReturns,
        NumPyException,
        NumPyYields,
        NumPyAttribute,
        NumPyWarning,
        NumPySeeAlsoItem,
        NumPyReference,
        NumPyMethod,
    }
)


class DOC002(
    BaseRule[
        GoogleArg
        | GoogleReturn
        | GoogleException
        | GoogleYield
        | GoogleAttribute
        | GoogleWarning
        | GoogleSeeAlsoItem
        | GoogleMethod
        | NumPyParameter
        | NumPyReturns
        | NumPyException
        | NumPyYields
        | NumPyAttribute
        | NumPyWarning
        | NumPySeeAlsoItem
        | NumPyReference
        | NumPyMethod
    ]
):
    """Incorrect indentation of a docstring section entry."""

    code = "DOC002"
    enabled_by_default = True

    def diagnose(
        self,
        node: GoogleArg
        | GoogleReturn
        | GoogleException
        | GoogleYield
        | GoogleAttribute
        | GoogleWarning
        | GoogleSeeAlsoItem
        | GoogleMethod
        | NumPyParameter
        | NumPyReturns
        | NumPyException
        | NumPyYields
        | NumPyAttribute
        | NumPyWarning
        | NumPySeeAlsoItem
        | NumPyReference
        | NumPyMethod,
        ctx: DiagnoseContext,
    ) -> Iterator[Diagnostic]:
        """Yield DOC002 diagnostics for incorrectly indented docstring entries."""
        ds_text = ctx.docstring_text

        # Find the start of the line on which this entry appears.
        before = ds_text[: node.range.start]
        last_nl = before.rfind("\n")
        if last_nl == -1:
            # Entry is on the very first line of the docstring content — skip.
            return
        line_start = last_nl + 1
        actual_indent = node.range.start - line_start

        # Determine section-level indentation from the docstring content.
        col_offset = getattr(ctx.docstring_stmt, "col_offset", 0)
        section_indent_str = detect_section_indent(ds_text, col_offset)
        section_indent = len(section_indent_str)

        # NumPy entries are at the same level as the section header;
        # Google entries are indented 4 more spaces.
        expected_indent = section_indent if type(node) in _NUMPY_ENTRY_TYPES else section_indent + 4

        if actual_indent == expected_indent:
            return

        yield self._make_diagnostic(
            ctx,
            f"Expected {expected_indent}-space indentation, found {actual_indent}.",
            fix=Fix(
                edits=[Edit(start=line_start, end=node.range.start, new_text=" " * expected_indent)],
                applicability=Applicability.SAFE,
            ),
            target=node,
        )
