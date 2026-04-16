"""Test fixture for PRM103: Parameter has no type in docstring (docstring style).

Expected: 1 violation(s) (PRM103)
Fix: unsafe
"""


def missing_docstring_type(x: int) -> None:
    """Do something.

    Args:
        x: Has signature annotation but no docstring type.
    """
    pass
