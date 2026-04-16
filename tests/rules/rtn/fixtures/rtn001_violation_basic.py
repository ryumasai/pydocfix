"""Test fixture for RTN001: Function has return annotation but no Returns section.

Expected: 1 violation(s) (RTN001)
Fix: unsafe
"""


def missing_returns_section(x: int) -> int:
    """Do something."""
    return x
