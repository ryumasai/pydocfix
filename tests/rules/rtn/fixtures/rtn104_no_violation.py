"""Test fixture for RTN104: Redundant return type in docstring (type_annotation_style = "signature").

Expected: 0 violations (RTN104)
Fix: yes
"""


def no_return_type_in_docstring() -> int:
    """Do something.

    Returns:
        The result with no type in docstring.
    """
    return 42
