# Fixture for PRM105: Parameter has no type annotation in signature (type_annotation_style = "signature").
# Requires Config(type_annotation_style="signature").


# violation
def no_signature_annotation(x) -> None:
    """Do something.

    Args:
        x: Has no signature annotation when signature style is required.
    """
    pass


# no violation
def has_signature_annotation(x: int) -> None:
    """Do something.

    Args:
        x: Has signature annotation.
    """
    pass
