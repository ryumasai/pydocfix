"""Test fixture for YLD106: Yield has signature annotation (type_annotation_style = "docstring").

Expected: 1 violation(s) (YLD106)
Fix: no
"""

from collections.abc import Iterator


def has_yield_signature_annotation() -> Iterator[int]:
    """Do something.

    Yields:
        int: The value.
    """
    yield 42
