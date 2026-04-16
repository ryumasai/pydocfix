"""Test fixture for RIS005: Exception documented but not raised.

Expected: 1 violation(s) (RIS005)
Fix: unsafe
"""


def extra_exception_in_raises():
    """Do something.

    Raises:
        ValueError: When value is wrong.
        TypeError: This exception is never raised.
    """
    raise ValueError("something went wrong")
