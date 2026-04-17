"""Test fixture for PRM005: Docstring has parameter not in function signature.

Expected: 0 violations (PRM005)
Fix: unsafe
"""


def all_exist(x: int, y: str) -> None:
    """Do something.

    Args:
        x (int): The first argument.
        y (str): The second argument.
    """
    pass
