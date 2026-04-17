# Fixture for YLD106: Yield has signature annotation (type_annotation_style = "docstring").
# Requires Config(type_annotation_style="docstring").

from collections.abc import Iterator


# violation
def has_yield_signature_annotation() -> Iterator[int]:
    """Do something.

    Yields:
        int: The value.
    """
    yield 42


# no violation
def no_yield_signature_annotation():
    """Do something.

    Yields:
        int: The value with type in docstring only.
    """
    yield 42
