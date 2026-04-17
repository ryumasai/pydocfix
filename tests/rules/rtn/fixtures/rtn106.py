# Fixture for RTN106: Return has signature annotation (type_annotation_style = "docstring").
# Requires Config(type_annotation_style="docstring").


# violation
def has_return_annotation() -> int:
    """Do something.

    Returns:
        int: The result with signature annotation when docstring style is required.
    """
    return 42


# no violation
def no_return_annotation():
    """Do something.

    Returns:
        int: The result with no signature annotation (uses docstring type only).
    """
    return 42
