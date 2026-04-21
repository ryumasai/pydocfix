# Fixture for YLD002: Non-generator function has Yields section.

from collections.abc import Iterator


# violation
def not_generator_has_yields() -> None:
    """Do something.

    Yields:
        int: This function doesn't actually yield anything.
    """
    pass


# no violation
def generator_with_yields() -> Iterator[int]:
    """Do something.

    Yields:
        int: The generated value.
    """
    yield 42


def not_generator_no_yields() -> None:
    """Do something without yielding."""
    pass
