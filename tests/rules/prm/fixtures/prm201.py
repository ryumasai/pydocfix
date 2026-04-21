# Fixture for PRM201: Parameter with default value missing 'optional' in docstring.


# violation
def missing_optional(x: int = 0) -> None:
    """Do something.

    Args:
        x (int): The argument with a default value but no 'optional' mention.
    """
    pass


# no violation
def has_optional(x: int = 0) -> None:
    """Do something.

    Args:
        x (int, optional): The argument with optional mention.
    """
    pass


def required_param(x: int) -> None:
    """Do something.

    Args:
        x (int): Required argument with no default.
    """
    pass
