# Fixture for RIS005: Exception documented but not raised.


# violation
def extra_exception_in_raises():
    """Do something.

    Raises:
        ValueError: When value is wrong.
        TypeError: This exception is never raised.
    """
    raise ValueError("something went wrong")


# no violation
def all_documented_exceptions_raised():
    """Do something.

    Raises:
        ValueError: When value is wrong.
    """
    raise ValueError("something went wrong")
