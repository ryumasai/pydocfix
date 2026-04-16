"""Test fixture for RTN103: Return has no type in docstring (type_annotation_style = "docstring").

Expected: 1 violation(s) (RTN103)
Fix: unsafe
"""


def missing_return_type_in_docstring() -> int:
    """Do something.

    Returns:
        The result with no type in docstring.
    """
    return 42
