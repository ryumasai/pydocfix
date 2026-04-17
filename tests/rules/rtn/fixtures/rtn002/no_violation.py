"""Test fixture for RTN002: Returns section present but function doesn't return a value.

Expected: 0 violations (RTN002)
Fix: yes
"""


def returns_value_with_section() -> int:
    """Do something.

    Returns:
        int: The result.
    """
    return 42


def no_section_no_return() -> None:
    """Do something without returning."""
    pass
