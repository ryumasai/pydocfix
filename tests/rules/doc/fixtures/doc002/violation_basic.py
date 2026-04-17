"""Test fixture for DOC002: Incorrect indentation of docstring entry.

Expected: 1 violation(s) (DOC002)
Fix: yes
"""


def wrong_indent(x: int) -> int:
    """Do something.

    Args:
      x: Under-indented entry (should be 8 spaces, got 6).
    """
    return x
