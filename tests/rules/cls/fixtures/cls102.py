# Fixture for CLS102: class docstring has a Yields section.


# violation: class docstring contains Yields section
class HasYieldsSection:
    """A class.

    Yields:
        int: Some value.
    """

    pass


# no violation: class docstring has no Yields section
class NoYieldsSection:
    """A class."""

    pass


# no violation: generator function (not class) has Yields section
def not_a_class():
    """A generator.

    Yields:
        int: Some value.
    """
    yield 42
