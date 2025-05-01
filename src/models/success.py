from typing import Callable
from src.models.result import _E, _T, _U, Result, ResultException


class Success(Result[_T, _E]):
    """Represents a successful operation with a value.

    Type Variables:
        _T: Type of the success value.
        _E: Type of the error value (not used in Success).

    Attributes:
        _value (_T): The value of the successful operation.
    """

    def __init__(self, value: _T):
        """Initializes a Success with a value.

        Args:
            value (_T): The success value.
        """
        self._value = value

    def __repr__(self) -> str:
        """Returns a string representation of the Success object."""
        return f"Success({self._value})"

    def __str__(self) -> str:
        """Returns a user-friendly string representation of the Success object."""
        return f"Successfully: {self._value}"

    def is_success(self) -> bool:
        return True

    def is_failure(self) -> bool:
        return False

    def map(self, func: Callable[[_T], _U]) -> "Result[_U, _E]":
        return Success(func(self._value))

    def flat_map(self, func: Callable[[_T], "Result[_U, _E]"]) -> "Result[_U, _E]":
        return func(self._value)

    def map_err(self, func: Callable[[_E], _U]) -> "Result[_T, _U]":
        return self

    def unwrap(self) -> _T:
        return self._value

    def unwrap_err(self) -> _E:
        raise ResultException()
