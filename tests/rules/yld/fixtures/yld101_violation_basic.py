"""Test fixture for YLD101: Docstring yield type doesn't match type hint.

Expected: 1 violation(s) (YLD101)
Fix: unsafe
"""

from collections.abc import Iterator


def yield_type_mismatch() -> Iterator[int]:
    """Do something.

    Yields:
        str: Wrong type in docstring.
    """
    yield 42
