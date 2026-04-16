"""Test fixture for RTN003: Returns section has no description.

Expected: 0 violations (RTN003)
Fix: no
"""


def has_return_description() -> int:
    """Do something.

    Returns:
        int: The computed result.
    """
    return 42
