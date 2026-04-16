"""Test fixture for PRM104: Redundant type in docstring (signature style).

Expected: 0 violations (PRM104)
Fix: yes
"""


def no_docstring_type(x: int) -> None:
    """Do something.

    Args:
        x: Relies on signature annotation only.
    """
    pass
