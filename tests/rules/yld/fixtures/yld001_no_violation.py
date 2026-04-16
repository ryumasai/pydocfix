"""Test fixture for YLD001: Generator function has no Yields section.

Expected: 0 violations (YLD001)
Fix: unsafe
"""

from collections.abc import Iterator


def has_yields_section() -> Iterator[int]:
    """Do something.

    Yields:
        int: The generated value.
    """
    yield 42


def not_a_generator() -> int:
    """Do something without yielding."""
    return 42
