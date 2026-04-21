# Fixture for YLD001: Generator function has no Yields section.
# Requires Config(skip_short_docstrings=False).

from collections.abc import Iterator


# violation
def missing_yields_section() -> Iterator[int]:
    """Do something."""
    yield 42


# no violation
def has_yields_section() -> Iterator[int]:
    """Do something.

    Yields:
        int: The generated value.
    """
    yield 42


def not_a_generator() -> int:
    """Do something without yielding."""
    return 42
