"""Test fixture for RTN101: Docstring return type doesn't match type hint.

Expected: 1 violation(s) (RTN101)
Fix: unsafe
"""


def return_type_mismatch() -> int:
    """Do something.

    Returns:
        str: Wrong type in docstring.
    """
    return 42
