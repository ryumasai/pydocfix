# Fixture for PRM001: Function has parameters but no Args/Parameters section.


# violation
def missing_args_section(x: int, y: str) -> None:
    """Do something."""
    pass


# no violation
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
