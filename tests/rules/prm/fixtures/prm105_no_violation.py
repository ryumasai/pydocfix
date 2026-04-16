"""Test fixture for PRM105: Parameter has no type annotation in signature (signature style).

Expected: 0 violations (PRM105)
Fix: no
"""


def has_signature_annotation(x: int) -> None:
    """Do something.

    Args:
        x: Has signature annotation.
    """
    pass
