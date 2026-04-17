"""Test fixture for PRM201: Parameter with default value missing 'optional' in docstring.

Expected: 1 violation(s) (PRM201)
Fix: unsafe
"""


def missing_optional(x: int = 0) -> None:
    """Do something.

    Args:
        x (int): The argument with a default value but no 'optional' mention.
    """
    pass
