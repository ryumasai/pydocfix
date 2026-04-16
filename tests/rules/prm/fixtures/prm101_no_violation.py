"""Test fixture for PRM101: Docstring parameter type doesn't match type hint.

Expected: 0 violations (PRM101)
Fix: unsafe
"""


def types_match(x: int, y: str) -> None:
    """Do something.

    Args:
        x (int): The integer argument.
        y (str): The string argument.
    """
    pass


def no_doc_type(x: int) -> None:
    """Do something.

    Args:
        x: No type in docstring, so no mismatch to check.
    """
    pass
