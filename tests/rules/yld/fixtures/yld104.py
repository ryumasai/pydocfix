# Fixture for YLD104: Redundant yield type in docstring (type_annotation_style = "signature").
# Requires Config(type_annotation_style="signature").

from collections.abc import Iterator


# violation
def redundant_yield_type_in_docstring() -> Iterator[int]:
    """Do something.

    Yields:
        int: Redundant type when signature style is required.
    """
    yield 42


# no violation
def no_yield_type_in_docstring() -> Iterator[int]:
    """Do something.

    Yields:
        The value with no type in docstring.
    """
    yield 42
