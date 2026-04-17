"""Test fixture for PRM001: Function has parameters but no Args section.

Expected: 0 violations (PRM001)
Fix: unsafe
"""


def has_args_section(x: int, y: str) -> None:
    """Do something.

    Args:
        x (int): The first argument.
        y (str): The second argument.
    """
    pass


def no_params() -> None:
    """Do something with no parameters."""
    pass
