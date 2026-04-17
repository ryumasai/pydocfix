"""Test fixture for RIS003: Raises entry has no description.

Expected: 1 violation(s) (RIS003)
Fix: no
"""


def empty_raises_description():
    """Do something.

    Raises:
        ValueError:
    """
    raise ValueError("something went wrong")
