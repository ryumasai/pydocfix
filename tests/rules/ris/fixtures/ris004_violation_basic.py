"""Test fixture for RIS004: Exception raised but not documented.

Expected: 1 violation(s) (RIS004)
Fix: unsafe
"""


def missing_exception_in_raises():
    """Do something.

    Raises:
        TypeError: When type is wrong.
    """
    raise ValueError("undocumented exception")
    raise TypeError("documented exception")
