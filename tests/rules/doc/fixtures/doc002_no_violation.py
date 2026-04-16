"""Test fixture for DOC002: Incorrect indentation of docstring entry.

Expected: 0 violations (DOC002)
Fix: yes
"""


def correct_indent(x: int) -> int:
    """Do something.

    Args:
        x: Correctly indented at 8 spaces.

    Returns:
        int: The result.
    """
    return x
