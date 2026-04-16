"""Test fixture for RTN101: Docstring return type doesn't match type hint.

Expected: 0 violations (RTN101)
Fix: unsafe
"""


def return_types_match() -> int:
    """Do something.

    Returns:
        int: The correct type in docstring.
    """
    return 42


def no_return_type_in_docstring() -> int:
    """Do something.

    Returns:
        The result with no type specified.
    """
    return 42
