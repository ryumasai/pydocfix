"""Test fixture for YLD102: Yield type not in docstring or signature.

Expected: 0 violations (YLD102)
Fix: no
"""

from collections.abc import Iterator


def type_in_signature() -> Iterator[int]:
    """Do something.

    Yields:
        The value.
    """
    yield 42


def type_in_docstring():
    """Do something.

    Yields:
        int: The value.
    """
    yield 42
