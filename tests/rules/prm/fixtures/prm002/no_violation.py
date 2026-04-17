"""Test fixture for PRM002: Function has no parameters but docstring has Args section.

Expected: 0 violations (PRM002)
Fix: yes
"""


def has_params_and_args(x: int) -> None:
    """Do something.

    Args:
        x (int): The argument.
    """
    pass


def no_params_no_args() -> None:
    """Do something with no parameters."""
    pass
