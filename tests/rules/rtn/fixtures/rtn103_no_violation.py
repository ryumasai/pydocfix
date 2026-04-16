"""Test fixture for RTN103: Return has no type in docstring (type_annotation_style = "docstring").

Expected: 0 violations (RTN103)
Fix: unsafe
"""


def has_return_type_in_docstring() -> int:
    """Do something.

    Returns:
        int: The result with type in docstring.
    """
    return 42
