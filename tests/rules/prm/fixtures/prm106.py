# Fixture for PRM106: Parameter has signature annotation (type_annotation_style = "docstring").
# Requires Config(type_annotation_style="docstring").


# violation
def has_signature_annotation(x: int) -> None:
    """Do something.

    Args:
        x (int): Has signature annotation when docstring style is required.
    """
    pass


# no violation
def no_signature_annotation(x) -> None:
    """Do something.

    Args:
        x (int): Uses only docstring type, no signature annotation.
    """
    pass
