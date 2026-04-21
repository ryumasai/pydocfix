# Fixture for PRM001 with class_docstring_style='init':
# __init__ should be skipped (CLS205 handles it); regular functions still flagged.
# Requires Config(class_docstring_style="init", skip_short_docstrings=False).


# violation: regular function with params but no Args section
def regular_function_missing_args(x: int, y: str) -> None:
    """Do something."""
    pass


# no violation: __init__ is skipped when class_docstring_style='init'
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
