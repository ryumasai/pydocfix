"""Test fixture for RIS005: Exception documented but not raised.

Expected: 0 violations (RIS005)
Fix: unsafe
"""


def all_documented_exceptions_raised():
    """Do something.

    Raises:
        ValueError: When value is wrong.
    """
    raise ValueError("something went wrong")
