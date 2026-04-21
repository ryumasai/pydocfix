# Fixture for PRM102: Parameter has no type in docstring or signature.


# violation
def no_type_anywhere(x) -> None:
    """Do something.

    Args:
        x: No type in docstring, no annotation in signature.
    """
    pass


# no violation
def type_in_signature(x: int) -> None:
    """Do something.

    Args:
        x: Has annotation in signature.
    """
    pass


def type_in_docstring(x) -> None:
    """Do something.

    Args:
        x (int): Has type in docstring.
    """
    pass
