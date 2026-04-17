"""Test fixture for RTN003: Returns section has no description.

Expected: 1 violation(s) (RTN003)
Fix: no
"""


def empty_return_description() -> int:
    """Do something.

    Returns:
        int:
    """
    return 42
