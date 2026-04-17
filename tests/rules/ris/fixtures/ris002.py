# Fixture for RIS002: Function has Raises section but doesn't raise.


# violation
def no_raise_has_raises_section():
    """Do something.

    Raises:
        ValueError: This function never actually raises.
    """
    return 42


# no violation
def raises_with_section():
    """Do something.

    Raises:
        ValueError: When something goes wrong.
    """
    raise ValueError("something went wrong")


def no_raise_no_section():
    """Do something without raising."""
    return 42
