"""Test fixture for YLD103: Yield has no type in docstring (type_annotation_style = "docstring").

Expected: 1 violation(s) (YLD103)
Fix: unsafe
"""

from collections.abc import Iterator


def missing_yield_type_in_docstring() -> Iterator[int]:
    """Do something.

    Yields:
        The value with no type in docstring.
    """
    yield 42
