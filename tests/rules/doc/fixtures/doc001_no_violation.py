"""Test fixture for DOC001: Docstring sections not in canonical order.

Expected: 0 violations (DOC001)
Fix: unsafe
"""


def correct_order(x: int) -> int:
    """Do something.

    Args:
        x (int): The input.

    Returns:
        int: The result.
    """
    return x


def args_only(x: int, y: str) -> None:
    """Do something.

    Args:
        x (int): The first argument.
        y (str): The second argument.
    """
    pass
