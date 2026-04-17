"""Test fixture for PRM008: Docstring parameter has empty description.

Expected: 0 violations (PRM008)
Fix: no
"""


def has_description(x: int) -> None:
    """Do something.

    Args:
        x (int): The input value.
    """
    pass
