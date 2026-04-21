# Fixture for CLS001: __init__ has its own docstring but the class also has one.


# violation: both class and __init__ have docstrings
class BothHaveDocstrings:
    """Class-level docstring."""

    def __init__(self, x: int) -> None:
        """Initialize with x."""
        self.x = x


# no violation: only class has a docstring
class OnlyClassDocstring:
    """Class-level docstring."""

    def __init__(self, x: int) -> None:
        self.x = x


# no violation: only __init__ has a docstring
class OnlyInitDocstring:
    def __init__(self, x: int) -> None:
        """Initialize with x."""
        self.x = x


# no violation: neither has a docstring
class NeitherHasDocstring:
    def __init__(self, x: int) -> None:
        self.x = x
