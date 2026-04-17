# Fixture for PRM008: Docstring parameter has empty description.


# violation
def empty_description(x: int) -> None:
    """Do something.

    Args:
        x (int):
    """
    pass


# no violation
def has_description(x: int) -> None:
    """Do something.

    Args:
        x (int): The input value.
    """
    pass
