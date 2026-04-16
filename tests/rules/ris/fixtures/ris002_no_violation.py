"""Test fixture for RIS002: Function has Raises section but doesn't raise.

Expected: 0 violations (RIS002)
Fix: yes
"""


def raises_with_section():
    """Do something.

    Raises:
        ValueError: When something goes wrong.
    """
    raise ValueError("something went wrong")


def no_raise_no_section():
    """Do something without raising."""
    return 42
