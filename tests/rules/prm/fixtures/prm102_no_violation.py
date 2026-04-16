"""Test fixture for PRM102: Parameter has no type in docstring or signature.

Expected: 0 violations (PRM102)
Fix: no
"""


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
