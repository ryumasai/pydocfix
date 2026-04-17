"""Test fixture for PRM106: Parameter has signature annotation (docstring style).

Expected: 1 violation(s) (PRM106)
Fix: no
"""


def has_signature_annotation(x: int) -> None:
    """Do something.

    Args:
        x (int): Has signature annotation when docstring style is required.
    """
    pass
