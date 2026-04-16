"""Test fixture for PRM009: Parameter name missing * or ** prefix.

Expected: 1 violation(s) (PRM009)
Fix: yes
"""


def missing_star_prefix(*args: int, **kwargs: str) -> None:
    """Do something.

    Args:
        args (int): Positional arguments without * prefix.
        kwargs (str): Keyword arguments without ** prefix.
    """
    pass
