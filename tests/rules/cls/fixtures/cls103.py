# Fixture for CLS103: class docstring has an Args section (class_docstring_style='init').
# Requires Config(class_docstring_style="init").


# violation: class docstring has Args section but style is 'init'
class HasArgsSectionInit:
    """A class.

    Args:
        x: The value.
    """

    def __init__(self, x: int) -> None:
        self.x = x


# no violation: class docstring has no Args section
class NoArgsSection:
    """A class."""

    def __init__(self, x: int) -> None:
        self.x = x


# no violation: it's __init__ not class
class OnlyInitHasArgs:
    """A class."""

    def __init__(self, x: int) -> None:
        """Initialize.

        Args:
            x: The value.
        """
        self.x = x
