"""Test fixture for RIS004: Exception raised but not documented.

Expected: 0 violations (RIS004)
Fix: unsafe
"""


def all_exceptions_documented():
    """Do something.

    Raises:
        ValueError: When value is wrong.
        TypeError: When type is wrong.
    """
    raise ValueError("something went wrong")
    raise TypeError("type error")
