# Fixture for YLD101: Docstring yield type doesn't match type hint.

from collections.abc import Iterator


# violation
def yield_type_mismatch() -> Iterator[int]:
    """Do something.

    Yields:
        str: Wrong type in docstring.
    """
    yield 42


# no violation
def yield_types_match() -> Iterator[int]:
    """Do something.

    Yields:
        int: The correct type in docstring.
    """
    yield 42


def no_yield_type_in_docstring() -> Iterator[int]:
    """Do something.

    Yields:
        The value with no type specified.
    """
    yield 42
