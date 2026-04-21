# Fixture for PRM003: Docstring documents self or cls.


# violation
class MyClassViolation:
    def my_method(self, x: int) -> None:
        """Do something.

        Args:
            self: The instance (should not be documented).
            x (int): The argument.
        """
        pass


# no violation
class MyClassNoViolation:
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
