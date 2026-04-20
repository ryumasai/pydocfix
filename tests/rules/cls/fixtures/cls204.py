# Fixture for CLS204: __init__ docstring has a Raises section (class_docstring_style='class').
# Requires Config(class_docstring_style="class").


# violation: __init__ docstring has Raises section but style is 'class'
class InitHasRaisesClass:
    def __init__(self, x: int) -> None:
        """Initialize.

        Raises:
            ValueError: If x is negative.
        """
        if x < 0:
            raise ValueError("x must be non-negative")
        self.x = x


# no violation: __init__ docstring has no Raises section
class CleanInit:
    def __init__(self, x: int) -> None:
        """Initialize."""
        self.x = x


# no violation: it's a regular method not __init__
class RegularMethod:
    def process(self, x: int) -> None:
        """Process.

        Raises:
            ValueError: On invalid input.
        """
        raise ValueError("invalid")
