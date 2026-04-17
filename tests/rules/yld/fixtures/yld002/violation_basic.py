"""Test fixture for YLD002: Non-generator function has Yields section.

Expected: 1 violation(s) (YLD002)
Fix: yes
"""


def not_generator_has_yields() -> None:
    """Do something.

    Yields:
        int: This function doesn't actually yield anything.
    """
    pass
