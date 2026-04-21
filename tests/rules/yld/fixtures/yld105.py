# Fixture for YLD105: Yield has no annotation in signature (type_annotation_style = "signature").
# Requires Config(type_annotation_style="signature").

from collections.abc import Iterator


# violation
def no_yield_annotation():
    """Do something.

    Yields:
        The value with no signature annotation.
    """
    yield 42


# no violation
def has_yield_annotation() -> Iterator[int]:
    """Do something.

    Yields:
        The value.
    """
    yield 42
