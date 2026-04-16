"""Test fixture for PRM102: Parameter has no type in docstring or signature.

Expected: 1 violation(s) (PRM102)
Fix: no
"""


def no_type_anywhere(x) -> None:
    """Do something.

    Args:
        x: No type in docstring, no annotation in signature.
    """
    pass
