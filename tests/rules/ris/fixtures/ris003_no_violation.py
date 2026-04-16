"""Test fixture for RIS003: Raises entry has no description.

Expected: 0 violations (RIS003)
Fix: no
"""


def has_raises_description():
    """Do something.

    Raises:
        ValueError: When something goes wrong.
    """
    raise ValueError("something went wrong")
