"""Test fixture for YLD101: Docstring yield type doesn't match type hint.

Expected: 0 violations (YLD101)
Fix: unsafe
"""

from collections.abc import Iterator


def yield_types_match() -> Iterator[int]:
    """Do something.

    Yields:
        int: The correct type in docstring.
    """
    yield 42


def no_yield_type_in_docstring() -> Iterator[int]:
    """Do something.

    Yields:
        The value with no type specified.
    """
    yield 42
