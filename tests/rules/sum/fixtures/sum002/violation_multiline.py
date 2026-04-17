"""Test fixture for SUM002: multiline docstring missing period on summary.

Expected: 1 violation(s) (SUM002)
Fix: yes
"""


def multiline_missing_period(x: int) -> int:
    """Do something with x

    Args:
        x (int): The input value.

    Returns:
        int: The result.
    """
    return x
