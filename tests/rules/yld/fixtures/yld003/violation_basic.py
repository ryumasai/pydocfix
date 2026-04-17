"""Test fixture for YLD003: Yields section has no description.

Expected: 1 violation(s) (YLD003)
Fix: no
"""

from collections.abc import Iterator


def empty_yields_description() -> Iterator[int]:
    """Do something.

    Yields:
        int:
    """
    yield 42
