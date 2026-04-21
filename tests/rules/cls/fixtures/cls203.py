# Fixture for CLS203: __init__ docstring has an Args section (class_docstring_style='class').
# Requires Config(class_docstring_style="class").


# violation: __init__ docstring has Args section but style is 'class'
class InitHasArgsClass:
    def __init__(self, x: int) -> None:
        """Initialize.

        Args:
            x: The value.
        """
        self.x = x


# no violation: __init__ docstring has no Args section
class CleanInit:
    def __init__(self, x: int) -> None:
        """Initialize."""
        self.x = x


# no violation: it's a regular method not __init__
class RegularMethod:
    def process(self, x: int) -> None:
        """Process.

        Args:
            x: The value.
        """
        pass
