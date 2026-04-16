"""Test fixture for YLD003: Yields section has no description.

Expected: 0 violations (YLD003)
Fix: no
"""

from collections.abc import Iterator


def has_yields_description() -> Iterator[int]:
    """Do something.

    Yields:
        int: The generated integer value.
    """
    yield 42
