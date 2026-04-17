# Fixture for DOC003: One-line docstring should be written on a single line.


# violation
def summary_only_multiline():
    """
    Do something.
    """
    pass

# violation: closing quotes on next line (no blank line)
def summary_closing_on_next_line():
    """Do something.
    """
    pass

# violation: extra blank line before closing quotes
def summary_only_blank_line():
    """Do something.

    """
    pass

# no violation: already single-line
def already_single_line():
    """Do something."""
    pass

# no violation: multiline summary
def multiline_summary():
    """Line one.
    Line two.
    """
    pass

# no violation: has extended summary (multiline is required)
def extended_summary():
    """Do something.

    Extended summary.
    """
    pass

# no violation: has sections (multiline is required)
def has_sections(x: int) -> None:
    """Do something.

    Args:
        x: A parameter.
    """
    pass
