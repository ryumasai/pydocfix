# Fixture for PRM009: Parameter name missing * or ** prefix.


# violation
def missing_star_prefix(*args: int, **kwargs: str) -> None:
    """Do something.

    Args:
        args (int): Positional arguments without * prefix.
        kwargs (str): Keyword arguments without ** prefix.
    """
    pass


# no violation
def with_star_prefix(*args: int, **kwargs: str) -> None:
    """Do something.

    Args:
        *args (int): Positional arguments with * prefix.
        **kwargs (str): Keyword arguments with ** prefix.
    """
    pass
