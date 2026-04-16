"""Test fixture for SUM001: Docstring has no summary line.

Expected: 1 violation(s) (SUM001)
Fix: no
"""


def no_summary():
    """
    Args:
        x: A parameter.
    """
    pass
