"""Test fixture for RTN102: Return type not in docstring or signature.

Expected: 1 violation(s) (RTN102)
Fix: no
"""


def no_return_type_anywhere():
    """Do something.

    Returns:
        The result with no type in docstring or signature.
    """
    return 42
