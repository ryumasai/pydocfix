"""Test fixture for RTN106: Return has signature annotation (type_annotation_style = "docstring").

Expected: 0 violations (RTN106)
Fix: no
"""


def no_return_annotation():
    """Do something.

    Returns:
        int: The result with no signature annotation (uses docstring type only).
    """
    return 42
