# Fixture for PRM007: Duplicate parameter in docstring.


# violation
def duplicate_param(x: int, y: str) -> None:
    """Do something.

    Args:
        x (int): The first argument.
        y (str): The second argument.
        x (int): Duplicate entry for x.
    """
    pass


# no violation
def no_duplicates(x: int, y: str) -> None:
    """Do something.

    Args:
        x (int): The first argument.
        y (str): The second argument.
    """
    pass
