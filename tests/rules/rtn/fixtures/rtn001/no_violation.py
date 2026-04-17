"""Test fixture for RTN001: Function has return annotation but no Returns section.

Expected: 0 violations (RTN001)
Fix: unsafe
"""


def has_returns_section(x: int) -> int:
    """Do something.

    Returns:
        int: The result.
    """
    return x


def no_return_annotation(x: int) -> None:
    """Do something without a return value."""
    pass
