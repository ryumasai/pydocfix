# Fixture for CLS202: __init__ docstring has a Yields section.


# violation: __init__ docstring contains Yields section
class InitHasYieldsSection:
    def __init__(self, x: int) -> None:
        """Initialize.

        Yields:
            int: Nothing.
        """
        self.x = x


# no violation: generator method (not __init__) has Yields section
class GeneratorMethod:
    def generate(self):
        """Generate items.

        Yields:
            int: Items.
        """
        yield 42


# no violation: __init__ docstring has no Yields section
class CleanInit:
    def __init__(self, x: int) -> None:
        """Initialize."""
        self.x = x
