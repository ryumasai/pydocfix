"""Test fixture for PRM003: Docstring documents self or cls.

Expected: 0 violations (PRM003)
Fix: yes
"""


class MyClass:
    def my_method(self, x: int) -> None:
        """Do something.

        Args:
            x (int): The argument.
        """
        pass

    @classmethod
    def class_method(cls, x: int) -> None:
        """Do something.

        Args:
            x (int): The argument.
        """
        pass
