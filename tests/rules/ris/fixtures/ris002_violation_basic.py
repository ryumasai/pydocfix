"""Test fixture for RIS002: Function has Raises section but doesn't raise.

Expected: 1 violation(s) (RIS002)
Fix: yes
"""


def no_raise_has_raises_section():
    """Do something.

    Raises:
        ValueError: This function never actually raises.
    """
    return 42
