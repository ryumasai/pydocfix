"""Test fixture for PRM007: Duplicate parameter in docstring.

Expected: 0 violations (PRM007)
Fix: unsafe
"""


def no_duplicates(x: int, y: str) -> None:
    """Do something.

    Args:
        x (int): The first argument.
        y (str): The second argument.
    """
    pass
