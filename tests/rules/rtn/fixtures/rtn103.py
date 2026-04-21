# Fixture for RTN103: Return has no type in docstring (type_annotation_style = "docstring").
# Requires Config(type_annotation_style="docstring").


# violation
def missing_return_type_in_docstring() -> int:
    """Do something.

    Returns:
        The result with no type in docstring.
    """
    return 42


# no violation
def has_return_type_in_docstring() -> int:
    """Do something.

    Returns:
        int: The result with type in docstring.
    """
    return 42
