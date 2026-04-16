"""Test fixture for YLD103: Yield has no type in docstring (type_annotation_style = "docstring").

Expected: 0 violations (YLD103)
Fix: unsafe
"""

from collections.abc import Iterator


def has_yield_type_in_docstring() -> Iterator[int]:
    """Do something.

    Yields:
        int: The value with type in docstring.
    """
    yield 42
