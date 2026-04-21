# Fixture for RIS004: Exception raised but not documented.


# violation
def missing_exception_in_raises():
    """Do something.

    Raises:
        TypeError: When type is wrong.
    """
    raise ValueError("undocumented exception")
    raise TypeError("documented exception")


# no violation
def all_exceptions_documented():
    """Do something.

    Raises:
        ValueError: When value is wrong.
        TypeError: When type is wrong.
    """
    raise ValueError("something went wrong")
    raise TypeError("type error")
