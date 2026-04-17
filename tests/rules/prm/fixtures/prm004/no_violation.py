"""Test fixture for PRM004: Missing parameter in docstring.

Expected: 0 violations (PRM004)
Fix: unsafe
"""


def all_documented(x: int, y: str) -> None:
    """Do something.

    Args:
        x (int): The first argument.
        y (str): The second argument.
    """
    pass
