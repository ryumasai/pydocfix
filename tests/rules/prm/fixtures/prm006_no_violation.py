"""Test fixture for PRM006: Docstring parameters in wrong order.

Expected: 0 violations (PRM006)
Fix: unsafe
"""


def correct_order(x: int, y: str) -> None:
    """Do something.

    Args:
        x (int): The first argument.
        y (str): The second argument.
    """
    pass
