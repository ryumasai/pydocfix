# Fixture for CLS105: class docstring missing Args section (class_docstring_style='class').
# Requires Config(class_docstring_style="class").


# violation: class docstring has no Args section but style is 'class' and __init__ has params
class MissingArgsSection:
    """A class.

    Does something useful.
    """

    def __init__(self, x: int, y: str) -> None:
        self.x = x
        self.y = y


# no violation: class docstring already has Args section
class HasArgsSection:
    """A class.

    Args:
        x: The x value.
    """

    def __init__(self, x: int) -> None:
        self.x = x


# no violation: __init__ has no parameters (besides self)
class NoParams:
    """A class."""

    def __init__(self) -> None:
        pass


# no violation: no __init__ method
class NoInit:
    """A class."""

    pass
