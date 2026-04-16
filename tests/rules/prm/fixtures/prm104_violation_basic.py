"""Test fixture for PRM104: Redundant type in docstring (signature style).

Expected: 1 violation(s) (PRM104)
Fix: yes
"""


def redundant_docstring_type(x: int) -> None:
    """Do something.

    Args:
        x (int): Has both signature annotation and docstring type (redundant).
    """
    pass
