"""Test fixture for YLD105: Yield has no annotation in signature (type_annotation_style = "signature").

Expected: 0 violations (YLD105)
Fix: no
"""

from collections.abc import Iterator


def has_yield_annotation() -> Iterator[int]:
    """Do something.

    Yields:
        The value.
    """
    yield 42
