"""Test fixture for YLD102: Yield type not in docstring or signature.

Expected: 1 violation(s) (YLD102)
Fix: no
"""


def no_yield_type_anywhere():
    """Do something.

    Yields:
        The value with no type anywhere.
    """
    yield 42
