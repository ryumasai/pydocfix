"""Test fixture for PRM103: Parameter has no type in docstring (docstring style).

Expected: 0 violations (PRM103)
Fix: unsafe
"""


def has_docstring_type(x: int) -> None:
    """Do something.

    Args:
        x (int): Has both signature annotation and docstring type.
    """
    pass
