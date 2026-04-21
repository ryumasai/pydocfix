# Fixture for PRM001 with class_docstring_style='class':
# __init__ should be skipped; regular functions still flagged.
# Requires Config(class_docstring_style="class", skip_short_docstrings=False).


# violation: regular function with params but no Args section
def regular_function_missing_args(x: int, y: str) -> None:
    """Do something."""
    pass


# no violation: __init__ is skipped when class_docstring_style='class'
class MyClass:
    """A class."""

    def __init__(self, x: int) -> None:
        """Initialize."""
        self.x = x


# no violation: regular function already has Args section
def regular_function_has_args(x: int) -> None:
    """Do something.

    Args:
        x (int): The value.
    """
    pass
