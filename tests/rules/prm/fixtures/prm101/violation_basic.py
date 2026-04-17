"""Test fixture for PRM101: Docstring parameter type doesn't match type hint.

Expected: 1 violation(s) (PRM101)
Fix: unsafe
"""


def type_mismatch(x: int) -> None:
    """Do something.

    Args:
        x (str): The argument documented as str but annotated as int.
    """
    pass
