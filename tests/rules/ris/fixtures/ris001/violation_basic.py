"""Test fixture for RIS001: Function raises but has no Raises section.

Expected: 1 violation(s) (RIS001)
Fix: unsafe
"""


def missing_raises_section():
    """Do something."""
    raise ValueError("something went wrong")
