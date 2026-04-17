"""Test fixture for SUM001: Docstring has no summary line.

Expected: 0 violations (SUM001)
Fix: no
"""


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
