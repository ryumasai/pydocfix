"""Test fixture for PRM005: Docstring has parameter not in function signature.

Expected: 1 violation(s) (PRM005)
Fix: unsafe
"""


def extra_param(x: int) -> None:
    """Do something.

    Args:
        x (int): The argument.
        z (str): This parameter does not exist.
    """
    pass
