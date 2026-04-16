"""Test fixture for PRM105: Parameter has no type annotation in signature (signature style).

Expected: 1 violation(s) (PRM105)
Fix: no
"""


def no_signature_annotation(x) -> None:
    """Do something.

    Args:
        x: Has no signature annotation when signature style is required.
    """
    pass
