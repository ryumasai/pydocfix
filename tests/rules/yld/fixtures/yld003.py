# Fixture for YLD003: Yields section has no description.

from collections.abc import Iterator


# violation
def empty_yields_description() -> Iterator[int]:
    """Do something.

    Yields:
        int:
    """
    yield 42


# no violation
def has_yields_description() -> Iterator[int]:
    """Do something.

    Yields:
        int: The generated integer value.
    """
    yield 42
