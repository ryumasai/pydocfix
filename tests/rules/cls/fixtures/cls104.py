# Fixture for CLS104: class docstring has a Raises section (class_docstring_style='init').
# Requires Config(class_docstring_style="init").


# violation: class docstring has Raises section but style is 'init'
class HasRaisesSectionInit:
    """A class.

    Raises:
        ValueError: If x is negative.
    """

    def __init__(self, x: int) -> None:
        if x < 0:
            raise ValueError("x must be non-negative")
        self.x = x


# no violation: class docstring has no Raises section
class NoRaisesSection:
    """A class."""

    def __init__(self, x: int) -> None:
        self.x = x


# no violation: it's __init__ not class
class OnlyInitHasRaises:
    """A class."""

    def __init__(self, x: int) -> None:
        """Initialize.

        Raises:
            ValueError: If x is negative.
        """
        if x < 0:
            raise ValueError("x must be non-negative")
        self.x = x
