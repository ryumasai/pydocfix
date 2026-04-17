# Fixture for PRM005: Docstring has parameter not in function signature.


# violation
def extra_param(x: int) -> None:
    """Do something.

    Args:
        x (int): The argument.
        z (str): This parameter does not exist.
    """
    pass


# no violation
def all_exist(x: int, y: str) -> None:
    """Do something.

    Args:
        x (int): The first argument.
        y (str): The second argument.
    """
    pass
