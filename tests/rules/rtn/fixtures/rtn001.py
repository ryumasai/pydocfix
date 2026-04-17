# Fixture for RTN001: Function has return annotation but no Returns section.
# Requires Config(skip_short_docstrings=False).


# violation
def missing_returns_section(x: int) -> int:
    """Do something."""
    return x


# no violation
def has_returns_section(x: int) -> int:
    """Do something.

    Returns:
        int: The result.
    """
    return x


def no_return_annotation(x: int) -> None:
    """Do something without a return value."""
    pass
