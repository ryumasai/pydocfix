# Fixture for CLS205: __init__ docstring missing Args section (class_docstring_style='init').
# Requires Config(class_docstring_style="init").


# violation: __init__ docstring has no Args section but style is 'init' and has params
class MissingArgsInit:
    def __init__(self, x: int, y: str) -> None:
        """Initialize."""
        self.x = x
        self.y = y


# no violation: __init__ docstring already has Args section
class HasArgsInit:
    def __init__(self, x: int) -> None:
        """Initialize.

        Args:
            x: The value.
        """
        self.x = x


# no violation: __init__ has no parameters (besides self)
class NoParams:
    def __init__(self) -> None:
        """Initialize."""
        pass


# no violation: it's a regular method not __init__
class RegularMethodMissingArgs:
    def process(self, x: int) -> None:
        """Process."""
        pass
