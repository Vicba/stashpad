"""CLI and storage exceptions with mapped exit codes."""

from __future__ import annotations


class StashError(Exception):
    """Base exception for Stash operations.

    Parameters
    ----------
    message : str
        Human-readable error description.

    Attributes
    ----------
    exit_code : int
        CLI exit code for this error class.
    message : str
        Error message text.

    Examples
    --------
    >>> err = StashError("something failed")
    >>> err.message
    'something failed'
    >>> err.exit_code
    1
    """

    exit_code: int = 1

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class VaultNotInitializedError(StashError):
    """Raised when the vault has not been initialized.

    Examples
    --------
    >>> VaultNotInitializedError.exit_code
    2
    """

    exit_code = 2


class EntryNotFoundError(StashError):
    """Raised when an entry ID does not exist.

    Examples
    --------
    >>> EntryNotFoundError.exit_code
    3
    """

    exit_code = 3


class StorageError(StashError):
    """Raised when reading or writing vault data fails.

    Examples
    --------
    >>> StorageError.exit_code
    4
    """

    exit_code = 4


class ValidationError(StashError):
    """Raised when user input fails validation.

    Examples
    --------
    >>> ValidationError.exit_code
    5
    """

    exit_code = 5
