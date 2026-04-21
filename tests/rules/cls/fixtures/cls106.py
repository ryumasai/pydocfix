# Fixture for CLS106: class docstring missing Raises section (class_docstring_style='class').
# Requires Config(class_docstring_style="class").


# violation: class docstring has no Raises section but style is 'class' and __init__ raises
class MissingRaisesSection:
    """A class.

    Args:
        x: The value.
    """

    def __init__(self, x: int) -> None:
        if x < 0:
            raise ValueError("x must be non-negative")
        self.x = x


# no violation: class docstring already has Raises section
class HasRaisesSection:
    """A class.

    Raises:
        ValueError: If x is negative.
    """

    def __init__(self, x: int) -> None:
        if x < 0:
            raise ValueError("x must be non-negative")
        self.x = x


# no violation: __init__ does not raise
class NoRaises:
    """A class."""

    def __init__(self, x: int) -> None:
        self.x = x


# no violation: no __init__ method
class NoInit:
    """A class."""

    pass
