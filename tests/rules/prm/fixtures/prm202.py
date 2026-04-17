# Fixture for PRM202: Parameter with default value missing 'default' in docstring.


# violation
def missing_default_mention(x: int = 42) -> None:
    """Do something.

    Args:
        x (int, optional): The argument value.
    """
    pass


# no violation
def has_default_mention(x: int = 42) -> None:
    """Do something.

    Args:
        x (int, optional): The argument. Defaults to 42.
    """
    pass


def required_param(x: int) -> None:
    """Do something.

    Args:
        x (int): Required argument with no default value.
    """
    pass
