# Fixture for PRM104: Redundant type in docstring (type_annotation_style = "signature").
# Requires Config(type_annotation_style="signature").


# violation
def redundant_docstring_type(x: int) -> None:
    """Do something.

    Args:
        x (int): Has both signature annotation and docstring type (redundant).
    """
    pass


# no violation
def no_docstring_type(x: int) -> None:
    """Do something.

    Args:
        x: Relies on signature annotation only.
    """
    pass
