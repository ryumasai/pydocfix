# Fixture for CLS206: __init__ docstring missing Raises section (class_docstring_style='init').
# Requires Config(class_docstring_style="init").


# violation: __init__ docstring has no Raises section but style is 'init' and raises
class MissingRaisesInit:
    def __init__(self, x: int) -> None:
        """Initialize.

        Args:
            x: The value.
        """
        if x < 0:
            raise ValueError("x must be non-negative")
        self.x = x


# no violation: __init__ docstring already has Raises section
class HasRaisesInit:
    def __init__(self, x: int) -> None:
        """Initialize.

        Raises:
            ValueError: If x is negative.
        """
        if x < 0:
            raise ValueError("x must be non-negative")
        self.x = x


# no violation: __init__ does not raise
class NoRaisesInit:
    def __init__(self, x: int) -> None:
        """Initialize."""
        self.x = x


# no violation: it's a regular method not __init__
class RegularMethodMissingRaises:
    def process(self, x: int) -> None:
        """Process."""
        raise ValueError("invalid")
