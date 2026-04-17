"""Test fixture for PRM001: Function has parameters but no Args section.

Expected: 1 violation(s) (PRM001)
Fix: unsafe
"""


def missing_args_section(x: int, y: str) -> None:
    """Do something."""
    pass
