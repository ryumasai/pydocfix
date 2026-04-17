"""Test fixture for YLD105: Yield has no annotation in signature (type_annotation_style = "signature").

Expected: 1 violation(s) (YLD105)
Fix: no
"""


def no_yield_annotation():
    """Do something.

    Yields:
        The value with no signature annotation.
    """
    yield 42
