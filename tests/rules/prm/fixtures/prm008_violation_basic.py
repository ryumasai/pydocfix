"""Test fixture for PRM008: Docstring parameter has empty description.

Expected: 1 violation(s) (PRM008)
Fix: no
"""


def empty_description(x: int) -> None:
    """Do something.

    Args:
        x (int):
    """
    pass
