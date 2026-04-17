"""Test fixture for PRM106: Parameter has signature annotation (docstring style).

Expected: 0 violations (PRM106)
Fix: no
"""


def no_signature_annotation(x) -> None:
    """Do something.

    Args:
        x (int): Uses only docstring type, no signature annotation.
    """
    pass
