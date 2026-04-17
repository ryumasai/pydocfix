"""Test fixture for RTN105: Return has no annotation in signature (type_annotation_style = "signature").

Expected: 1 violation(s) (RTN105)
Fix: no
"""


def no_return_annotation():
    """Do something.

    Returns:
        The result with no signature annotation.
    """
    return 42
