# Fixture for CLS101: class docstring has a Returns section.


# violation: class docstring contains Returns section
class HasReturnsSection:
    """A class.

    Returns:
        int: Some value.
    """

    pass


# no violation: class docstring has no Returns section
class NoReturnsSection:
    """A class."""

    pass


# no violation: method (not class) has Returns section
def not_a_class() -> int:
    """A function.

    Returns:
        int: Some value.
    """
    return 42
