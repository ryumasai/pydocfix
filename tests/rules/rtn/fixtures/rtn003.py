# Fixture for RTN003: Returns section has no description.


# violation
def empty_return_description() -> int:
    """Do something.

    Returns:
        int:
    """
    return 42


# no violation
def has_return_description() -> int:
    """Do something.

    Returns:
        int: The computed result.
    """
    return 42
