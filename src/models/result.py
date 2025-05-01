from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Callable

_T = TypeVar("_T")
_E = TypeVar("_E")
_U = TypeVar("_U")


class ResultException(Exception):
    """Custom exception for Result class.

    Attributes:
        message (str): Explanation of the exception.
    """

    def __init__(self, message: str = "Cannot unwrap error from a Success"):
        """Initializes the ResultException with a message.

        Args:
            message (str): Explanation of the exception.
        """
        super().__init__(message)
        self.message = message


class Result(Generic[_T, _E], ABC):
    """Abstract base class for Result, representing success or failure cases.

    Type Variables:
        _T: Type of the success value.
        _E: Type of the error value.

    """

    @abstractmethod
    def is_success(self) -> bool:
        """Checks if the Result represents a success.

        Returns:
            bool: True if the Result is a success, False otherwise.
        """

    @abstractmethod
    def is_failure(self) -> bool:
        """Checks if the Result represents a failure.

        Returns:
            bool: True if the Result is a failure, False otherwise.
        """

    @abstractmethod
    def map(self, func: Callable[[_T], _U]) -> "Result[_U, _E]":
        """Maps the success value to another value using the provided function.

        Args:
            func (Callable[[_T], _U]): Function to map the success value.

        Returns:
            Result[_U, _E]: A new Result containing the mapped value.
        """

    @abstractmethod
    def flat_map(self, func: Callable[[_T], "Result[_U, _E]"]) -> "Result[_U, _E]":
        """Maps the success value to another Result using the provided function.

        Args:
            func (Callable[[_T], Result[_U, _E]]): Function to map the success value.

        Returns:
            Result[_U, _E]: The mapped Result.
        """

    @abstractmethod
    def map_err(self, func: Callable[[_E], _U]) -> "Result[_T, _U]":
        """Maps the error value to another value using the provided function.

        Args:
            func (Callable[[_E], _U]): Function to map the error value.

        Returns:
            Result[_T, _U]: A new Result containing the mapped error.
        """

    @abstractmethod
    def unwrap(self) -> _T:
        """Extracts the success value, if available.

        Returns:
            _T: The success value.

        Raises:
            ResultException: If the Result is a failure.
        """

    @abstractmethod
    def unwrap_err(self) -> _E:
        """Extracts the error value, if available.

        Returns:
            _E: The error value.

        Raises:
            ResultException: If the Result is a success.
        """
