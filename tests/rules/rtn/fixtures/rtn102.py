# Fixture for RTN102: Return type not in docstring or signature.


# violation
def no_return_type_anywhere():
    """Do something.

    Returns:
        The result with no type in docstring or signature.
    """
    return 42


# no violation
def type_in_signature() -> int:
    """Do something.

    Returns:
        The result.
    """
    return 42


def type_in_docstring():
    """Do something.

    Returns:
        int: The result.
    """
    return 42
