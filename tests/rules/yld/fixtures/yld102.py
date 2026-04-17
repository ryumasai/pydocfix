# Fixture for YLD102: Yield type not in docstring or signature.

from collections.abc import Iterator


# violation
def no_yield_type_anywhere():
    """Do something.

    Yields:
        The value with no type anywhere.
    """
    yield 42


# no violation
def type_in_signature() -> Iterator[int]:
    """Do something.

    Yields:
        The value.
    """
    yield 42


def type_in_docstring():
    """Do something.

    Yields:
        int: The value.
    """
    yield 42
