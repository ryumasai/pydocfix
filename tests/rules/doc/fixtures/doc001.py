# Fixture for DOC001: Docstring sections not in canonical order.


# violation
def wrong_order(x: int) -> int:
    """Do something.

    Returns:
        int: The result.

    Args:
        x (int): The input.
    """
    return x


# no violation
def correct_order(x: int) -> int:
    """Do something.

    Args:
        x (int): The input.

    Returns:
        int: The result.
    """
    return x


def args_only(x: int, y: str) -> None:
    """Do something.

    Args:
        x (int): The first argument.
        y (str): The second argument.
    """
    pass
