# Fixture for SUM001: Docstring has no summary line.


# violation
def no_summary():
    """
    Args:
        x: A parameter.
    """
    pass


# no violation
def has_summary():
    """Does something."""
    pass


def has_summary_with_sections(x: int) -> int:
    """Does something.

    Args:
        x (int): The input.

    Returns:
        int: The result.
    """
    return x
