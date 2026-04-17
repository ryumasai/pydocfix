# Fixture for RTN101: Docstring return type doesn't match type hint.


# violation
def return_type_mismatch() -> int:
    """Do something.

    Returns:
        str: Wrong type in docstring.
    """
    return 42


# no violation
def return_types_match() -> int:
    """Do something.

    Returns:
        int: The correct type in docstring.
    """
    return 42


def no_return_type_in_docstring() -> int:
    """Do something.

    Returns:
        The result with no type specified.
    """
    return 42
