# Fixture for CLS201: __init__ docstring has a Returns section.


# violation: __init__ docstring contains Returns section
class InitHasReturnsSection:
    def __init__(self, x: int) -> None:
        """Initialize.

        Returns:
            None: Nothing.
        """
        self.x = x


# no violation: regular method (not __init__) has Returns section
class RegularMethod:
    def regular_method(self) -> int:
        """Do something.

        Returns:
            int: The result.
        """
        return 42


# no violation: __init__ docstring has no Returns section
class CleanInit:
    def __init__(self, x: int) -> None:
        """Initialize."""
        self.x = x
