# Fixture for SUM002: Summary should end with a period.


# violation
def missing_period():
    """Do something"""
    pass


def multiline_missing_period(x: int) -> int:
    """Do something with x

    Args:
        x (int): The input value.

    Returns:
        int: The result.
    """
    return x


# no violation
def has_period():
    """Do something."""
    pass


def ends_with_exclamation():
    """Be careful!"""
    pass


def ends_with_question():
    """Is this safe?"""
    pass
