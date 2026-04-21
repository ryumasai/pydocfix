# Fixture for RTN104: Redundant return type in docstring (type_annotation_style = "signature").
# Requires Config(type_annotation_style="signature").


# violation
def redundant_return_type_in_docstring() -> int:
    """Do something.

    Returns:
        int: Redundant type when signature style is required.
    """
    return 42


# no violation
def no_return_type_in_docstring() -> int:
    """Do something.

    Returns:
        The result with no type in docstring.
    """
    return 42
