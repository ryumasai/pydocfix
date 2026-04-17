"""Test fixture for RTN104: Redundant return type in docstring (type_annotation_style = "signature").

Expected: 1 violation(s) (RTN104)
Fix: yes
"""


def redundant_return_type_in_docstring() -> int:
    """Do something.

    Returns:
        int: Redundant type when signature style is required.
    """
    return 42
