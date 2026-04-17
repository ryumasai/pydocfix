"""Test fixture for DOC001: Docstring sections not in canonical order.

Expected: 1 violation(s) (DOC001)
Fix: unsafe
"""


def wrong_order(x: int) -> int:
    """Do something.

    Returns:
        int: The result.

    Args:
        x (int): The input.
    """
    return x
