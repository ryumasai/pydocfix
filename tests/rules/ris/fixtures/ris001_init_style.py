# Fixture for RIS001 with class_docstring_style='init':
# __init__ should be skipped (CLS206 handles it); regular functions still flagged.
# Requires Config(class_docstring_style="init", skip_short_docstrings=False).


# violation: regular function raises but has no Raises section
def regular_function_missing_raises() -> None:
    """Do something."""
    raise ValueError("error")


# no violation: __init__ is skipped when class_docstring_style='init'
class MyClass:
    """A class."""

    def __init__(self, x: int) -> None:
        """Initialize."""
        if x < 0:
            raise ValueError("x must be non-negative")
        self.x = x


# no violation: regular function already has Raises section
def regular_function_has_raises() -> None:
    """Do something.

    Raises:
        ValueError: On error.
    """
    raise ValueError("error")
