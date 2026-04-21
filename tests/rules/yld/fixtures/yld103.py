# Fixture for YLD103: Yield has no type in docstring (type_annotation_style = "docstring").
# Requires Config(type_annotation_style="docstring").

from collections.abc import Iterator


# violation
def missing_yield_type_in_docstring() -> Iterator[int]:
    """Do something.

    Yields:
        The value with no type in docstring.
    """
    yield 42


# no violation
def has_yield_type_in_docstring() -> Iterator[int]:
    """Do something.

    Yields:
        int: The value with type in docstring.
    """
    yield 42
