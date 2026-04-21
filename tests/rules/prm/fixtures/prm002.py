# Fixture for PRM002: Function has no parameters but docstring has Args section.


# violation
def no_params_has_args():
    """Do something.

    Args:
        x: A parameter that does not exist.
    """
    pass


# no violation
def has_params_and_args(x: int) -> None:
    """Do something.

    Args:
        x (int): The argument.
    """
    pass


def no_params_no_args() -> None:
    """Do something with no parameters."""
    pass
