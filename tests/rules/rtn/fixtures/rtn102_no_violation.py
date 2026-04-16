"""Test fixture for RTN102: Return type not in docstring or signature.

Expected: 0 violations (RTN102)
Fix: no
"""


def type_in_signature() -> int:
    """Do something.

    Returns:
        The result.
    """
    return 42


def type_in_docstring():
    """Do something.

    Returns:
        int: The result.
    """
    return 42
