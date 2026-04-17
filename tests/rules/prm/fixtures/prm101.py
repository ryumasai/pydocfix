# Fixture for PRM101: Docstring parameter type doesn't match type hint.


# violation
def type_mismatch(x: int) -> None:
    """Do something.

    Args:
        x (str): The argument documented as str but annotated as int.
    """
    pass


# no violation
def types_match(x: int, y: str) -> None:
    """Do something.

    Args:
        x (int): The integer argument.
        y (str): The string argument.
    """
    pass


def no_doc_type(x: int) -> None:
    """Do something.

    Args:
        x: No type in docstring, so no mismatch to check.
    """
    pass
