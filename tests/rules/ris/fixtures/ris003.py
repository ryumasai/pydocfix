# Fixture for RIS003: Raises entry has no description.


# violation
def empty_raises_description():
    """Do something.

    Raises:
        ValueError:
    """
    raise ValueError("something went wrong")


# no violation
def has_raises_description():
    """Do something.

    Raises:
        ValueError: When something goes wrong.
    """
    raise ValueError("something went wrong")
