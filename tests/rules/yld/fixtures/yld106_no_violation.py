"""Test fixture for YLD106: Yield has signature annotation (type_annotation_style = "docstring").

Expected: 0 violations (YLD106)
Fix: no
"""


def no_yield_signature_annotation():
    """Do something.

    Yields:
        int: The value with type in docstring only.
    """
    yield 42
