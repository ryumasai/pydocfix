# Fixture for PRM006: Docstring parameters in wrong order.


# violation
def wrong_param_order(x: int, y: str) -> None:
    """Do something.

    Args:
        y (str): The second argument.
        x (int): The first argument.
    """
    pass


# no violation
def correct_order(x: int, y: str) -> None:
    """Do something.

    Args:
        x (int): The first argument.
        y (str): The second argument.
    """
    pass
