"""Test fixture for PRM002: Function has no parameters but docstring has Args section.

Expected: 1 violation(s) (PRM002)
Fix: yes
"""


def no_params_has_args():
    """Do something.

    Args:
        x: A parameter that does not exist.
    """
    pass
