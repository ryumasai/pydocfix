"""Test fixture for YLD104: Redundant yield type in docstring (type_annotation_style = "signature").

Expected: 0 violations (YLD104)
Fix: yes
"""

from collections.abc import Iterator


def no_yield_type_in_docstring() -> Iterator[int]:
    """Do something.

    Yields:
        The value with no type in docstring.
    """
    yield 42
