"""Test fixture for RTN106: Return has signature annotation (type_annotation_style = "docstring").

Expected: 1 violation(s) (RTN106)
Fix: no
"""


def has_return_annotation() -> int:
    """Do something.

    Returns:
        int: The result with signature annotation when docstring style is required.
    """
    return 42
