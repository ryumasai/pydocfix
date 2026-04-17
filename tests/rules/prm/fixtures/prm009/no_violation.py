"""Test fixture for PRM009: Parameter name missing * or ** prefix.

Expected: 0 violations (PRM009)
Fix: yes
"""


def with_star_prefix(*args: int, **kwargs: str) -> None:
    """Do something.

    Args:
        *args (int): Positional arguments with * prefix.
        **kwargs (str): Keyword arguments with ** prefix.
    """
    pass
