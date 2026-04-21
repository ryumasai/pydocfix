# Fixture for RIS001: Function raises but has no Raises section.
# Requires Config(skip_short_docstrings=False).


# violation
def missing_raises_section():
    """Do something."""
    raise ValueError("something went wrong")


# no violation
def has_raises_section():
    """Do something.

    Raises:
        ValueError: When something goes wrong.
    """
    raise ValueError("something went wrong")


def no_raises():
    """Do something without raising."""
    return 42
