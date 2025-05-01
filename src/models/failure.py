from typing import Callable
from src.models.result import _E, _T, _U, Result, ResultException


class Failure(Result[_T, _E]):
    """Represents a failed operation with an error.

    Type Variables:
        _T: Type of the success value (not used in Failure).
        _E: Type of the error value.

    Attributes:
        _error (_E): The error value of the failed operation.
    """

    def __init__(self, error: _E):
        """Initializes a Failure with an error.

        Args:
            error (_E): The error value.
        """
        self._error = error

    def __repr__(self) -> str:
        """Returns a string representation of the Failure object."""
        return f"Failure({self._error})"

    def __str__(self) -> str:
        """Returns a user-friendly string representation of the Failure object."""
        return f"Failed with: {self._error}"

    def is_success(self) -> bool:
        return False

    def is_failure(self) -> bool:
        return True

    def map(self, func: Callable[[_T], _U]) -> "Result[_U, _E]":
        return self

    def flat_map(self, func: Callable[[_T], "Result[_U, _E]"]) -> "Result[_U, _E]":
        return self

    def map_err(self, func: Callable[[_E], _U]) -> "Result[_T, _U]":
        return Failure(func(self._error))

    def unwrap(self) -> _T:
        raise ResultException()

    def unwrap_err(self) -> _E:
        return self._error
