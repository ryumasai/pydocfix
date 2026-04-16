"""Test fixture for PRM007: Duplicate parameter in docstring.

Expected: 1 violation(s) (PRM007)
Fix: unsafe
"""


def duplicate_param(x: int, y: str) -> None:
    """Do something.

    Args:
        x (int): The first argument.
        y (str): The second argument.
        x (int): Duplicate entry for x.
    """
    pass
