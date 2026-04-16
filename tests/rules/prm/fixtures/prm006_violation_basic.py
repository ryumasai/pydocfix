"""Test fixture for PRM006: Docstring parameters in wrong order.

Expected: 1 violation(s) (PRM006)
Fix: unsafe
"""


def wrong_param_order(x: int, y: str) -> None:
    """Do something.

    Args:
        y (str): The second argument.
        x (int): The first argument.
    """
    pass
