# Fixture for DOC002: Incorrect indentation of docstring entry.


# violation
def wrong_indent(x: int) -> int:
    """Do something.

    Args:
      x: Under-indented entry (should be 8 spaces, got 6).
    """
    return x


# no violation
def correct_indent(x: int) -> int:
    """Do something.

    Args:
        x: Correctly indented at 8 spaces.

    Returns:
        int: The result.
    """
    return x
