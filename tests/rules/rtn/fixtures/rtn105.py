# Fixture for RTN105: Return has no annotation in signature (type_annotation_style = "signature").
# Requires Config(type_annotation_style="signature").


# violation
def no_return_annotation():
    """Do something.

    Returns:
        The result with no signature annotation.
    """
    return 42


# no violation
def has_return_annotation() -> int:
    """Do something.

    Returns:
        The result with signature annotation.
    """
    return 42
