# Fixture for PRM103: Parameter has no type in docstring (type_annotation_style = "docstring").
# Requires Config(type_annotation_style="docstring").


# violation
def missing_docstring_type(x: int) -> None:
    """Do something.

    Args:
        x: Has signature annotation but no docstring type.
    """
    pass


# no violation
def has_docstring_type(x: int) -> None:
    """Do something.

    Args:
        x (int): Has both signature annotation and docstring type.
    """
    pass
