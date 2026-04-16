"""Test fixture for RTN105: Return has no annotation in signature (type_annotation_style = "signature").

Expected: 0 violations (RTN105)
Fix: no
"""


def has_return_annotation() -> int:
    """Do something.

    Returns:
        The result with signature annotation.
    """
    return 42
