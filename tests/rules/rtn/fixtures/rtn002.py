# Fixture for RTN002: Returns section present but function doesn't return a value.


# violation
def no_return_but_has_section() -> None:
    """Do something.

    Returns:
        None: This function doesn't actually return a value.
    """
    pass


# no violation
def returns_value_with_section() -> int:
    """Do something.

    Returns:
        int: The result.
    """
    return 42


def no_section_no_return() -> None:
    """Do something without returning."""
    pass
