"""Test fixture for PRM004: Missing parameter in docstring.

Expected: 1 violation(s) (PRM004)
Fix: unsafe
"""


def missing_param(x: int, y: str) -> None:
    """Do something.

    Args:
        x (int): The first argument.
    """
    pass
