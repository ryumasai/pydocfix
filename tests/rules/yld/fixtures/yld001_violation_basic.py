"""Test fixture for YLD001: Generator function has no Yields section.

Expected: 1 violation(s) (YLD001)
Fix: unsafe
"""

from collections.abc import Iterator


def missing_yields_section() -> Iterator[int]:
    """Do something."""
    yield 42
