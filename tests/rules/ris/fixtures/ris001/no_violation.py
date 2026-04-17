"""Test fixture for RIS001: Function raises but has no Raises section.

Expected: 0 violations (RIS001)
Fix: unsafe
"""


def has_raises_section():
    """Do something.

    Raises:
        ValueError: When something goes wrong.
    """
    raise ValueError("something went wrong")


def no_raises():
    """Do something without raising."""
    return 42
