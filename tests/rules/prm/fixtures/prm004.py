# Fixture for PRM004: Missing parameter in docstring.


# violation
def missing_param(x: int, y: str) -> None:
    """Do something.

    Args:
        x (int): The first argument.
    """
    pass


# no violation
def all_documented(x: int, y: str) -> None:
    """Do something.

    Args:
        x (int): The first argument.
        y (str): The second argument.
    """
    pass
