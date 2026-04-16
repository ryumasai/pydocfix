"""Test fixture for RTN002: Returns section present but function doesn't return a value.

Expected: 1 violation(s) (RTN002)
Fix: yes
"""


def no_return_but_has_section() -> None:
    """Do something.

    Returns:
        None: This function doesn't actually return a value.
    """
    pass
