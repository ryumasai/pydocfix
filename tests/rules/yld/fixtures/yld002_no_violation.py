"""Test fixture for YLD002: Non-generator function has Yields section.

Expected: 0 violations (YLD002)
Fix: yes
"""

from collections.abc import Iterator


def generator_with_yields() -> Iterator[int]:
    """Do something.

    Yields:
        int: The generated value.
    """
    yield 42


def not_generator_no_yields() -> None:
    """Do something without yielding."""
    pass
